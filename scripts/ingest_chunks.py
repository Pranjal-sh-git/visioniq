"""Chunk Ingestion Service for Azure AI Search.

Embeds and ingests chunked product documentation into Azure AI Search index "product-chunks".
Follows docs/rag_design.md:
  - Preflight validation with exact failure message requirement
  - Schema: chunk_id (key), product_id, product_name, category, section, title, content,
    content_vector (1536 dims, HNSW, cosine), token_count, is_synthetic
  - Semantic configuration enabled if tier supports it
  - Batch size 16 with exponential backoff on 429
  - Idempotent merge-or-upload with optional --recreate flag
  - Logs total embedding tokens used
"""

import argparse
import json
import logging
from pathlib import Path
import sys
import time
from typing import Any, Dict, List

# Ensure workspace root and backend are on sys.path
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
for directory in (str(ROOT_DIR), str(ROOT_DIR / "backend")):
    if directory not in sys.path:
        sys.path.insert(0, directory)

from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SearchableField,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    VectorSearch,
    VectorSearchAlgorithmMetric,
    VectorSearchProfile,
)

from backend.config import settings
from services.llm import get_azure_openai_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("visioniq.ingest_chunks")

INDEX_NAME = settings.AZURE_SEARCH_CHUNKS_INDEX or "product-chunks"
VECTOR_PROFILE_NAME = "chunk-vector-profile"
ALGORITHM_CONFIG_NAME = "chunk-hnsw-config"
EMBEDDING_DIM = 1536


def run_preflight_check() -> None:
    """Preflight check: embed one test string with the configured embedding deployment.

    If missing or errors, STOP and print exact error message.
    """
    deployment = settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
    logger.info(f"Running preflight check for embedding deployment: '{deployment}'...")

    if not deployment:
        print("Embedding deployment not found. Deploy text-embedding-3-small in Azure Portal and set AZURE_OPENAI_EMBEDDING_DEPLOYMENT.")
        sys.exit(1)

    try:
        openai_client = get_azure_openai_client()
        res = openai_client.embeddings.create(
            input=["VisionIQ preflight test string"],
            model=deployment,
        )
        if not res.data or len(res.data[0].embedding) != EMBEDDING_DIM:
            raise ValueError(f"Unexpected embedding dimension: {len(res.data[0].embedding) if res.data else 0}")
        logger.info(f"Preflight check PASSED! Model: '{deployment}', Dimensions: {EMBEDDING_DIM}, Tokens: {res.usage.total_tokens}")
    except Exception as e:
        logger.error(f"Preflight error: {e}")
        print("Embedding deployment not found. Deploy text-embedding-3-small in Azure Portal and set AZURE_OPENAI_EMBEDDING_DEPLOYMENT.")
        sys.exit(1)


def get_search_index_client() -> SearchIndexClient:
    endpoint = settings.AZURE_SEARCH_ENDPOINT
    key = settings.AZURE_SEARCH_KEY
    if not endpoint or not key:
        raise ValueError("AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_KEY must be configured in .env.")
    return SearchIndexClient(endpoint=endpoint, credential=AzureKeyCredential(key))


def get_chunks_search_client() -> SearchClient:
    endpoint = settings.AZURE_SEARCH_ENDPOINT
    key = settings.AZURE_SEARCH_KEY
    return SearchClient(
        endpoint=endpoint,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(key),
    )


def build_index_schema(supports_semantic: bool) -> SearchIndex:
    """Constructs the SearchIndex object for product-chunks."""
    fields = [
        SimpleField(name="chunk_id", type=SearchFieldDataType.String, key=True, filterable=True),
        SimpleField(name="product_id", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SearchableField(name="product_name", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="section", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SearchableField(name="title", type=SearchFieldDataType.String),
        SearchableField(name="content", type=SearchFieldDataType.String, analyzer_name="standard"),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=EMBEDDING_DIM,
            vector_search_profile_name=VECTOR_PROFILE_NAME,
        ),
        SimpleField(name="token_count", type=SearchFieldDataType.Int32, filterable=True),
        SimpleField(name="is_synthetic", type=SearchFieldDataType.Boolean, filterable=True),
    ]

    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name=ALGORITHM_CONFIG_NAME,
                parameters=HnswParameters(
                    metric=VectorSearchAlgorithmMetric.COSINE,
                    m=4,
                    ef_construction=400,
                    ef_search=500,
                ),
            )
        ],
        profiles=[
            VectorSearchProfile(
                name=VECTOR_PROFILE_NAME,
                algorithm_configuration_name=ALGORITHM_CONFIG_NAME,
            )
        ],
    )

    semantic_search = None
    if supports_semantic:
        semantic_config = SemanticConfiguration(
            name="chunk-semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name="title"),
                content_fields=[SemanticField(field_name="content")],
                keywords_fields=[
                    SemanticField(field_name="section"),
                    SemanticField(field_name="category"),
                ],
            ),
        )
        semantic_search = SemanticSearch(configurations=[semantic_config])

    return SearchIndex(
        name=INDEX_NAME,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search,
    )


def create_or_update_index(recreate: bool = False) -> bool:
    """Creates product-chunks index if it does not exist, or recreates if requested."""
    index_client = get_search_index_client()
    existing_indices = list(index_client.list_index_names())

    if INDEX_NAME in existing_indices:
        if recreate:
            logger.info(f"Recreating index '{INDEX_NAME}' (deleting existing)...")
            index_client.delete_index(INDEX_NAME)
        else:
            logger.info(f"Index '{INDEX_NAME}' already exists. Ingesting documents with merge-or-upload...")
            return True

    # Test whether semantic search is supported
    supports_semantic = True
    index_schema = build_index_schema(supports_semantic=True)
    try:
        logger.info(f"Creating index '{INDEX_NAME}' with semantic configuration...")
        index_client.create_index(index_schema)
        logger.info(f"Index '{INDEX_NAME}' created successfully with semantic search enabled!")
    except HttpResponseError as e:
        if "semantic" in str(e).lower() or "tier" in str(e).lower():
            logger.warning(f"Semantic search not supported on current tier ({e.message}). Falling back without semantic config...")
            supports_semantic = False
            index_schema = build_index_schema(supports_semantic=False)
            index_client.create_index(index_schema)
            logger.info(f"Index '{INDEX_NAME}' created successfully without semantic search.")
        else:
            raise

    return supports_semantic


def embed_batch_with_retry(openai_client, texts: List[str], deployment: str, max_retries: int = 5) -> tuple[List[List[float]], int]:
    """Generates embeddings for a batch of texts with exponential backoff on 429."""
    for attempt in range(max_retries):
        try:
            res = openai_client.embeddings.create(input=texts, model=deployment)
            vectors = [item.embedding for item in res.data]
            tokens_used = res.usage.total_tokens if res.usage else 0
            return vectors, tokens_used
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                wait_time = (2 ** attempt) + 1
                logger.warning(f"Rate limited (429) on batch. Waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                time.sleep(wait_time)
            else:
                logger.error(f"Error embedding batch: {e}")
                raise

    raise RuntimeError("Max retries exceeded while embedding batch.")


def ingest_all_chunks(chunks_file: Path, batch_size: int = 16) -> None:
    """Reads chunks.jsonl, embeds in batches of 16, and uploads to Azure AI Search."""
    if not chunks_file.exists():
        raise FileNotFoundError(f"Chunks file not found at: {chunks_file}")

    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks = [json.loads(line) for line in f if line.strip()]

    total_chunks = len(chunks)
    logger.info(f"Loaded {total_chunks} chunks from {chunks_file}")

    openai_client = get_azure_openai_client()
    search_client = get_chunks_search_client()
    deployment = settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT

    total_tokens_used = 0
    start_time = time.perf_counter()

    for i in range(0, total_chunks, batch_size):
        batch = chunks[i : i + batch_size]
        texts = [c["content"] for c in batch]
        
        vectors, tokens = embed_batch_with_retry(openai_client, texts, deployment)
        total_tokens_used += tokens

        documents_to_upload = []
        for chunk, vector in zip(batch, vectors):
            doc = {
                "chunk_id": chunk["chunk_id"],
                "product_id": chunk["product_id"],
                "product_name": chunk["product_name"],
                "category": chunk["category"],
                "section": chunk["section"],
                "title": chunk["title"],
                "content": chunk["content"],
                "content_vector": vector,
                "token_count": chunk["token_count"],
                "is_synthetic": chunk["is_synthetic"],
            }
            documents_to_upload.append(doc)

        search_client.merge_or_upload_documents(documents=documents_to_upload)
        logger.info(f"Ingested batch {i // batch_size + 1}/{(total_chunks + batch_size - 1) // batch_size} ({len(batch)} chunks)")

    elapsed = time.perf_counter() - start_time

    # Verification
    time.sleep(2)  # brief wait for indexing consistency
    doc_count = search_client.get_document_count()

    print("\n" + "=" * 70)
    print("INGESTION & INDEX VERIFICATION SUMMARY")
    print("=" * 70)
    print(f"Target Index:                  {INDEX_NAME}")
    print(f"Embedding Model Deployment:    {deployment} ({EMBEDDING_DIM} dims)")
    print(f"Total Chunks in chunks.jsonl:  {total_chunks}")
    print(f"Documents Verified in Index:   {doc_count}")
    print(f"Total Embedding Tokens Used:   {total_tokens_used:,}")
    print(f"Elapsed Time:                  {elapsed:.2f}s ({elapsed / total_chunks:.3f}s per chunk)")
    print(f"Count Match:                   {'MATCHED (100%)' if doc_count == total_chunks else 'MISMATCH'}")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Ingest product chunks into Azure AI Search")
    parser.add_argument("--chunks", default="data/corpus/chunks.jsonl", help="Path to chunks.jsonl")
    parser.add_argument("--batch-size", type=int, default=16, help="Embedding and upload batch size")
    parser.add_argument("--recreate", action="store_true", help="Delete and recreate index before ingestion")
    args = parser.parse_args()

    chunks_path = ROOT_DIR / args.chunks

    # 1. Preflight Check
    run_preflight_check()

    # 2. Schema creation
    create_or_update_index(recreate=args.recreate)

    # 3. Ingestion & verification
    ingest_all_chunks(chunks_path, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
