"""Product Matcher & Visual Identification Service.

Uses CLIP image embeddings to perform vector similarity search against the
Azure AI Search "product-catalog" index and return top matching products.
"""

import json
import logging
from pathlib import Path
import sys
from typing import Any, Optional, Union
from PIL import Image

# Ensure workspace root and backend are on sys.path
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent.parent
for directory in (str(ROOT_DIR), str(ROOT_DIR / "backend")):
    if directory not in sys.path:
        sys.path.insert(0, directory)

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

try:
    from backend.config import settings
except ImportError:
    from config import settings

from services.product_search.embeddings import generate_image_embedding, generate_text_embedding

logger = logging.getLogger(__name__)
INDEX_NAME = "product-catalog"

# Azure AI Search cosine score formula: (1 + cosine_similarity) / 2
# A score >= 0.85 corresponds to true cosine similarity >= 0.70
DEFAULT_CONFIDENCE_THRESHOLD = 0.85


def get_search_client() -> SearchClient:
    """Returns an authenticated SearchClient for the product-catalog index."""
    endpoint = settings.AZURE_SEARCH_ENDPOINT
    key = settings.AZURE_SEARCH_KEY

    if not endpoint or not key:
        raise ValueError("AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_KEY must be configured.")

    return SearchClient(
        endpoint=endpoint,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(key),
    )


def identify_product(
    image: Union[str, bytes, Path, Image.Image],
    top_k: int = 3,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    category_filter: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Identifies products from an uploaded image using vector similarity in Azure AI Search.

    Args:
        image: Local image file path, HTTP/HTTPS URL, raw image bytes, or PIL Image.
        top_k (int): Number of top matches to return (default: 3).
        confidence_threshold (float): Minimum similarity score for confident match (default: 0.85).
        category_filter (Optional[str]): Optional category to filter results (e.g. 'Headphones').

    Returns:
        list[dict[str, Any]]: Top-k matching products with similarity scores, confidence flags, and metadata.
    """
    logger.info("Generating embedding for candidate image...")
    image_vector = generate_image_embedding(image)

    search_client = get_search_client()

    vector_query = VectorizedQuery(
        vector=image_vector,
        k_nearest_neighbors=top_k,
        fields="image_vector",
    )

    filter_expression = f"category eq '{category_filter}'" if category_filter else None

    logger.info(f"Querying Azure AI Search '{INDEX_NAME}' with top_k={top_k}...")
    search_results = search_client.search(
        search_text=None,
        vector_queries=[vector_query],
        filter=filter_expression,
        select=["id", "name", "brand", "category", "description", "specifications", "features", "image_urls"],
        top=top_k,
    )

    matches = []
    for doc in search_results:
        specs_raw = doc.get("specifications")
        specs = {}
        if isinstance(specs_raw, str):
            try:
                specs = json.loads(specs_raw)
            except Exception:
                specs = {"raw": specs_raw}
        elif isinstance(specs_raw, dict):
            specs = specs_raw

        score = round(float(doc.get("@search.score", 0.0)), 4)
        is_confident = score >= confidence_threshold

        match_item = {
            "id": doc.get("id"),
            "name": doc.get("name"),
            "brand": doc.get("brand"),
            "category": doc.get("category"),
            "description": doc.get("description"),
            "specifications": specs,
            "features": doc.get("features", []),
            "image_urls": doc.get("image_urls", []),
            "similarity_score": score,
            "is_confident_match": is_confident,
            "confidence_threshold": confidence_threshold,
            "match_status": "confident_match" if is_confident else "no_confident_match",
        }
        matches.append(match_item)

    logger.info(f"Found {len(matches)} matching products.")
    return matches


def identify_product_by_text(
    query_text: str,
    top_k: int = 3,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> list[dict[str, Any]]:
    """Identifies products using a text query embedded into the same multimodal CLIP space.

    Args:
        query_text (str): Natural language query describing the product.
        top_k (int): Number of top matches to return.
        confidence_threshold (float): Minimum similarity score for confident match.

    Returns:
        list[dict[str, Any]]: Top-k matching products.
    """
    text_vector = generate_text_embedding(query_text)
    search_client = get_search_client()

    vector_query = VectorizedQuery(
        vector=text_vector,
        k_nearest_neighbors=top_k,
        fields="image_vector",
    )

    search_results = search_client.search(
        search_text=None,
        vector_queries=[vector_query],
        select=["id", "name", "brand", "category", "description", "specifications", "features", "image_urls"],
        top=top_k,
    )

    matches = []
    for doc in search_results:
        specs_raw = doc.get("specifications")
        try:
            specs = json.loads(specs_raw) if isinstance(specs_raw, str) else specs_raw
        except Exception:
            specs = {}

        score = round(float(doc.get("@search.score", 0.0)), 4)
        is_confident = score >= confidence_threshold

        matches.append({
            "id": doc.get("id"),
            "name": doc.get("name"),
            "brand": doc.get("brand"),
            "category": doc.get("category"),
            "description": doc.get("description"),
            "specifications": specs,
            "features": doc.get("features", []),
            "image_urls": doc.get("image_urls", []),
            "similarity_score": score,
            "is_confident_match": is_confident,
            "confidence_threshold": confidence_threshold,
            "match_status": "confident_match" if is_confident else "no_confident_match",
        })

    return matches


if __name__ == "__main__":
    sample_image = sys.argv[1] if len(sys.argv) > 1 else "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=800&q=80"
    print(f"Testing identify_product() with sample image: {sample_image}\n")
    try:
        results = identify_product(sample_image, top_k=3)
        print(f"=== TOP {len(results)} MATCHES ===")
        for i, match in enumerate(results, 1):
            print(f"{i}. [{match['id']}] {match['brand']} - {match['name']} (Score: {match['similarity_score']} | Status: {match['match_status']})")
            print(f"   Category: {match['category']}")
            print(f"   Description: {match['description'][:100]}...")
            print()
    except Exception as err:
        print(f"Error testing identify_product: {err}")
