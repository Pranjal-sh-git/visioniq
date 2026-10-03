"""scripts/test_retrieval.py - Retrieval smoke test for product-chunks index.

Tests 5 representative queries both with and without product_id filter across:
1. Vector-only (HNSW cosine similarity)
2. BM25-only (lexical search on content, title, product_name)
3. Hybrid RRF (Reciprocal Rank Fusion of BM25 + Vector)

Prints top-3 chunk_ids and scores for each combination.
"""

import os
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
for directory in (str(ROOT_DIR), str(ROOT_DIR / "backend")):
    if directory not in sys.path:
        sys.path.insert(0, directory)

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

from backend.config import settings
from services.llm import get_azure_openai_client

SMOKE_QUERIES = [
    {
        "query": "how long does the battery last",
        "product_id": "P001",
        "product_name": "Sony WH-1000XM5 Wireless Headphones",
        "category": "Headphone",
    },
    {
        "query": "how do I adjust the lumbar support",
        "product_id": "P010",
        "product_name": "Autonomous ErgoChair Pro",
        "category": "Chair",
    },
    {
        "query": "how do I clean these shoes",
        "product_id": "P019",
        "product_name": "Salomon XT-6 Trail Running Shoes",
        "category": "Shoe",
    },
    {
        "query": "does it track heart rate",
        "product_id": "P023",
        "product_name": "Samsung Galaxy Watch 6 Classic",
        "category": "Watch",
    },
    {
        "query": "what is the return process",
        "product_id": "P002",
        "product_name": "Bose QuietComfort Ultra Headphones",
        "category": "Any / Policy",
    },
]


def get_embedding(client, text: str, deployment: str) -> List[float]:
    resp = client.embeddings.create(input=[text], model=deployment)
    return resp.data[0].embedding


def run_retrieval(
    client: SearchClient,
    query_text: str,
    vector: List[float],
    mode: str,
    filter_expr: Optional[str] = None,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    vector_query = VectorizedQuery(
        vector=vector,
        k_nearest_neighbors=top_k,
        fields="content_vector",
    ) if mode in ("vector", "hybrid") else None

    search_text = query_text if mode in ("bm25", "hybrid") else None

    vector_queries = [vector_query] if vector_query else None

    results = client.search(
        search_text=search_text,
        vector_queries=vector_queries,
        filter=filter_expr,
        select=["chunk_id", "product_id", "section", "title"],
        top=top_k,
    )

    out = []
    for r in results:
        out.append({
            "chunk_id": r["chunk_id"],
            "product_id": r["product_id"],
            "title": r["title"],
            "score": round(r["@search.score"], 4),
        })
    return out


def main():
    if not settings.AZURE_SEARCH_ENDPOINT or not settings.AZURE_SEARCH_KEY:
        print("ERROR: Azure Search endpoint or key missing.")
        sys.exit(1)

    aoai_client = get_azure_openai_client()
    embedding_deployment = settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT or "text-embedding-3-small"
    index_name = settings.AZURE_SEARCH_CHUNKS_INDEX or "product-chunks"

    search_client = SearchClient(
        endpoint=settings.AZURE_SEARCH_ENDPOINT,
        index_name=index_name,
        credential=AzureKeyCredential(settings.AZURE_SEARCH_KEY),
    )

    print("=" * 80)
    print(f"RETRIEVAL SMOKE TESTS ON '{index_name}'")
    print("=" * 80)

    for idx, item in enumerate(SMOKE_QUERIES, 1):
        q = item["query"]
        pid = item["product_id"]
        pname = item["product_name"]

        print(f"\n[{idx}/5] Query: \"{q}\"")
        print(f"      Target: {pid} ({pname})")

        # Compute query vector
        q_vec = get_embedding(aoai_client, q, embedding_deployment)

        for filter_desc, filter_expr in [("Without Filter", None), (f"Filtered (product_id eq '{pid}')", f"product_id eq '{pid}'")]:
            print(f"\n  --- Mode: {filter_desc} ---")
            for mode_name in ["vector", "bm25", "hybrid"]:
                hits = run_retrieval(search_client, q, q_vec, mode_name, filter_expr, top_k=3)
                hits_str = ", ".join([f"{h['chunk_id']} (score: {h['score']})" for h in hits]) if hits else "No results"
                print(f"    * {mode_name.upper():<7}: {hits_str}")

    print("\n" + "=" * 80)
    print("SMOKE TESTS COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()
