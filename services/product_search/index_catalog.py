"""Catalog Indexing Service for Azure AI Search.

Creates the "product-catalog" vector search index in Azure AI Search and
indexes all 25 products with their 512-dim CLIP embeddings and metadata.
"""

import json
import logging
from pathlib import Path
import sys
from typing import Any

# Ensure workspace root and backend are on sys.path
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent.parent
for directory in (str(ROOT_DIR), str(ROOT_DIR / "backend")):
    if directory not in sys.path:
        sys.path.insert(0, directory)

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SearchableField,
    SimpleField,
    VectorSearch,
    VectorSearchAlgorithmMetric,
    VectorSearchProfile,
)

try:
    from backend.config import settings
except ImportError:
    from config import settings

from services.product_search.embeddings import (
    EMBEDDING_DIM,
    generate_image_embedding,
    generate_text_embedding,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

INDEX_NAME = "product-catalog"
VECTOR_PROFILE_NAME = "product-vector-profile"
ALGORITHM_CONFIG_NAME = "product-hnsw-config"
PRODUCTS_JSON_PATH = ROOT_DIR / "data" / "products" / "products.json"


def get_search_index_client() -> SearchIndexClient:
    """Instantiates SearchIndexClient using environment variables from config."""
    endpoint = settings.AZURE_SEARCH_ENDPOINT
    key = settings.AZURE_SEARCH_KEY

    if not endpoint or not key:
        raise ValueError(
            "AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_KEY must be set in your .env file."
        )

    return SearchIndexClient(endpoint=endpoint, credential=AzureKeyCredential(key))


def get_search_client() -> SearchClient:
    """Instantiates SearchClient for the product-catalog index."""
    endpoint = settings.AZURE_SEARCH_ENDPOINT
    key = settings.AZURE_SEARCH_KEY
    return SearchClient(
        endpoint=endpoint,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(key),
    )


def create_or_update_index() -> SearchIndex:
    """Defines and provisions the Azure AI Search vector index for products."""
    index_client = get_search_index_client()

    fields = [
        SimpleField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,
            filterable=True,
            sortable=True,
        ),
        SearchableField(
            name="name",
            type=SearchFieldDataType.String,
            filterable=True,
            sortable=True,
        ),
        SearchableField(
            name="brand",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True,
        ),
        SearchableField(
            name="category",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True,
        ),
        SearchableField(
            name="description",
            type=SearchFieldDataType.String,
        ),
        SearchableField(
            name="specifications",
            type=SearchFieldDataType.String,
        ),
        SearchField(
            name="features",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            searchable=True,
        ),
        SearchField(
            name="image_urls",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
        ),
        SearchField(
            name="image_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=EMBEDDING_DIM,
            vector_search_profile_name=VECTOR_PROFILE_NAME,
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name=ALGORITHM_CONFIG_NAME,
                parameters=HnswParameters(metric=VectorSearchAlgorithmMetric.COSINE),
            )
        ],
        profiles=[
            VectorSearchProfile(
                name=VECTOR_PROFILE_NAME,
                algorithm_configuration_name=ALGORITHM_CONFIG_NAME,
            )
        ],
    )

    index = SearchIndex(name=INDEX_NAME, fields=fields, vector_search=vector_search)
    logger.info(f"Creating or updating Azure AI Search index '{INDEX_NAME}'...")
    created_index = index_client.create_or_update_index(index)
    logger.info(f"Index '{INDEX_NAME}' provisioned successfully.")
    return created_index


def load_products_from_json() -> list[dict[str, Any]]:
    """Loads the products dataset from data/products/products.json."""
    if not PRODUCTS_JSON_PATH.exists():
        raise FileNotFoundError(f"Products file not found at: {PRODUCTS_JSON_PATH}")

    with open(PRODUCTS_JSON_PATH, "r", encoding="utf-8") as f:
        products = json.load(f)
    return products


def index_all_products():
    """Generates embeddings for all products and uploads them to Azure AI Search."""
    create_or_update_index()
    products = load_products_from_json()
    logger.info(f"Loaded {len(products)} products from {PRODUCTS_JSON_PATH}")

    search_client = get_search_client()
    documents_to_upload = []

    for idx, product in enumerate(products, 1):
        product_id = product.get("id")
        name = product.get("name")
        brand = product.get("brand")
        category = product.get("category")
        description = product.get("description", "")
        specifications = product.get("specifications", {})
        features = product.get("features", [])
        image_urls = product.get("image_urls", [])

        logger.info(f"[{idx}/{len(products)}] Processing product {product_id}: {name} ({brand})")

        # Generate embedding from reference image URL
        embedding = None
        if image_urls:
            try:
                first_image_url = image_urls[0]
                logger.info(f"  Downloading and embedding reference image: {first_image_url[:60]}...")
                embedding = generate_image_embedding(first_image_url)
            except Exception as e:
                logger.warning(f"  Image download failed ({e}), falling back to text description embedding")

        if embedding is None:
            # Multimodal fallback: compute text embedding in the same CLIP space
            composite_text = f"{name} by {brand}. Category: {category}. {description}"
            embedding = generate_text_embedding(composite_text)

        doc = {
            "id": product_id,
            "name": name,
            "brand": brand,
            "category": category,
            "description": description,
            "specifications": json.dumps(specifications),
            "features": features,
            "image_urls": image_urls,
            "image_vector": embedding,
        }
        documents_to_upload.append(doc)

    logger.info(f"Uploading {len(documents_to_upload)} documents to index '{INDEX_NAME}'...")
    result = search_client.upload_documents(documents=documents_to_upload)
    succeeded = sum(1 for r in result if r.succeeded)
    logger.info(f"Successfully indexed {succeeded}/{len(documents_to_upload)} products into Azure AI Search.")
    return succeeded


if __name__ == "__main__":
    index_all_products()
