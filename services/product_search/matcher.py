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


# Valid product categories present in the indexed catalog
CATALOG_CATEGORIES = {"Headphones", "Chairs", "Shoes", "Watches"}

CATEGORY_SYNONYMS: dict[str, list[str]] = {
    "Headphones": [
        "headphone", "headphones", "earphone", "earphones", "headset", "headsets",
        "earbud", "earbuds", "audio", "over-ear", "in-ear", "on-ear", "airpods"
    ],
    "Chairs": [
        "chair", "chairs", "furniture", "seating", "office chair", "desk chair",
        "ergonomic chair", "armchair", "seat", "stool"
    ],
    "Shoes": [
        "shoe", "shoes", "footwear", "sneaker", "sneakers", "running shoe",
        "running shoes", "trainer", "trainers", "boot", "boots", "cleat", "cleats",
        "sandal", "sandals", "footware"
    ],
    "Watches": [
        "watch", "watches", "smartwatch", "smartwatches", "timepiece", "timepieces",
        "chronograph", "wrist watch", "wrist-watch", "wristwatch"
    ],
}


def map_to_catalog_category(identified_info: Optional[dict[str, Any]]) -> Optional[str]:
    """Maps open-world identified metadata to an existing catalog category if relevant.

    Returns:
        Optional[str]: One of 'Headphones', 'Chairs', 'Shoes', 'Watches' if matched, otherwise None.
    """
    if not identified_info:
        return None

    cat_raw = (identified_info.get("category") or "").strip().lower()
    name_raw = (identified_info.get("product_name") or identified_info.get("model") or "").strip().lower()

    # Exact or synonym category match
    for cat_name, synonyms in CATEGORY_SYNONYMS.items():
        if cat_raw == cat_name.lower():
            return cat_name
        for syn in synonyms:
            if syn in cat_raw:
                return cat_name

    # Check product name or model if category was generic (e.g. 'Electronics' or 'Apparel')
    for cat_name, synonyms in CATEGORY_SYNONYMS.items():
        for syn in synonyms:
            if syn in name_raw:
                return cat_name

    return None


def find_similar_catalog_products(
    image: Optional[Union[str, bytes, Path, Image.Image]] = None,
    identified_info: Optional[dict[str, Any]] = None,
    query_text: Optional[str] = None,
    top_k: int = 3,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> list[dict[str, Any]]:
    """Searches the indexed catalog for similar product recommendations.

    Enforces category relevance: if the identified product belongs to a category
    NOT present in our catalog (e.g. smartphones, laptops, apparel), no recommendations
    are returned to avoid misleading cross-category high similarity scores.

    Args:
        image: Optional image input to embed.
        identified_info: Optional open-world product recognition dict (brand, model, category).
        query_text: Optional text query fallback.
        top_k: Number of similar items to retrieve.
        confidence_threshold: Similarity score threshold.

    Returns:
        list[dict[str, Any]]: Similar catalog items with scores, specs, and match flags.
    """
    # Category relevance check for open-world identification
    target_category: Optional[str] = None
    if identified_info:
        target_category = map_to_catalog_category(identified_info)
        if target_category is None:
            raw_cat = identified_info.get("category", "Unknown")
            logger.info(
                f"[CATALOG RELEVANCE] Identified category '{raw_cat}' is not in catalog categories ({CATALOG_CATEGORIES}). "
                "Suppressing catalog recommendations."
            )
            return []

    matches: list[dict[str, Any]] = []

    # Priority 1: Search using image vector if provided (filtered by relevant catalog category if known)
    if image is not None:
        try:
            matches = identify_product(
                image=image,
                top_k=top_k,
                confidence_threshold=confidence_threshold,
                category_filter=target_category,
            )
        except Exception as e:
            logger.warning(f"Image vector search failed in find_similar_catalog_products: {e}")

    # Priority 2: Supplement / fallback with open-world text query if vector search returned few matches
    if not matches and identified_info and target_category:
        brand = identified_info.get("brand", "")
        model = identified_info.get("model", "")
        combined_text = f"{brand} {model} {target_category}".strip()
        if combined_text and combined_text != "Unknown":
            try:
                matches = identify_product_by_text(
                    query_text=combined_text,
                    top_k=top_k,
                    confidence_threshold=confidence_threshold,
                )
                # Ensure strictly filtered by target_category
                matches = [m for m in matches if m.get("category") == target_category]
            except Exception as e:
                logger.warning(f"Text vector search failed in find_similar_catalog_products: {e}")

    # Priority 3: query_text fallback
    if not matches and query_text:
        matches = identify_product_by_text(
            query_text=query_text,
            top_k=top_k,
            confidence_threshold=confidence_threshold,
        )
        if target_category:
            matches = [m for m in matches if m.get("category") == target_category]

    # Format recommendations with similarity reasoning
    recommendations = []
    for item in matches:
        score = item.get("similarity_score", 0.0)
        is_exact = False
        if identified_info:
            target_brand = (identified_info.get("brand") or "").lower()
            target_model = (identified_info.get("model") or "").lower()
            item_name = (item.get("name") or "").lower()
            item_brand = (item.get("brand") or "").lower()
            if target_brand and target_brand in item_brand and target_model and target_model in item_name:
                is_exact = True

        rec_item = dict(item)
        rec_item["is_exact_catalog_match"] = is_exact
        rec_item["recommendation_reason"] = (
            f"Catalog item in '{item.get('category')}' with {int(score * 100)}% visual/textual similarity."
        )
        recommendations.append(rec_item)

    return recommendations



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
