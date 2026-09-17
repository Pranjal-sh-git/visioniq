"""RAG Service for Product Catalog Knowledge Retrieval and Answering.

Queries Azure AI Search for grounded product context and provides grounded,
hallucination-free answers based strictly on catalog specifications.
"""

import json
import logging
from pathlib import Path
import sys
from typing import Any, Optional

# Ensure workspace root and backend are on sys.path
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent.parent
for directory in (str(ROOT_DIR), str(ROOT_DIR / "backend")):
    if directory not in sys.path:
        sys.path.insert(0, directory)

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

try:
    from backend.config import settings
except ImportError:
    from config import settings

logger = logging.getLogger(__name__)
INDEX_NAME = "product-catalog"


def get_search_client() -> SearchClient:
    """Returns authenticated Azure SearchClient."""
    return SearchClient(
        endpoint=settings.AZURE_SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(settings.AZURE_SEARCH_KEY),
    )


def retrieve_product_by_id(product_id: str) -> Optional[dict[str, Any]]:
    """Retrieves a product directly by its ID from Azure AI Search."""
    search_client = get_search_client()
    try:
        doc = search_client.get_document(key=product_id)
        specs_raw = doc.get("specifications")
        specs = json.loads(specs_raw) if isinstance(specs_raw, str) else (specs_raw or {})
        doc["specifications"] = specs
        return doc
    except Exception as e:
        logger.warning(f"Product {product_id} not found: {e}")
        return None


def answer_product_question(product_id: Optional[str], question: str) -> dict[str, Any]:
    """Answers questions regarding a specific product grounded strictly in catalog data.

    Returns:
        dict: Contains answer, grounded_field, catalog_value, and is_available flag.
    """
    if not product_id:
        return {
            "product_id": None,
            "question": question,
            "answer": "Which product are you asking about? Please specify the product name or ID.",
            "requires_clarification": True,
            "is_available": False,
            "grounded_field": None,
            "catalog_value": None,
        }

    product = retrieve_product_by_id(product_id)
    if not product:
        return {
            "product_id": product_id,
            "question": question,
            "answer": f"Product '{product_id}' was not found in the catalog.",
            "requires_clarification": True,
            "is_available": False,
            "catalog_value": None,
        }

    name = product.get("name", "")
    brand = product.get("brand", "")
    specs = product.get("specifications", {})
    description = product.get("description", "")
    features = product.get("features", [])

    # Avoid duplicate brand name prefix if name already contains it
    display_name = name if name.lower().startswith(brand.lower()) else f"{brand} {name}".strip()

    q_lower = question.lower()

    # Match against specifications dictionary keys
    matched_value = None
    matched_field = None

    for key, val in specs.items():
        key_normalized = key.replace("_", " ").lower()
        if key_normalized in q_lower or any(word in q_lower for word in key_normalized.split()):
            matched_value = val
            matched_field = key
            break

    if matched_value:
        answer = f"The {matched_field.replace('_', ' ')} of the {display_name} is {matched_value}."
        return {
            "product_id": product_id,
            "product_name": name,
            "question": question,
            "answer": answer,
            "requires_clarification": False,
            "is_available": True,
            "grounded_field": matched_field,
            "catalog_value": matched_value,
            "hallucination": False,
        }

    # If field is absent from catalog specifications
    return {
        "product_id": product_id,
        "product_name": name,
        "question": question,
        "answer": f"This information is not specified in the product catalog for {display_name}.",
        "requires_clarification": False,
        "is_available": False,
        "grounded_field": None,
        "catalog_value": None,
        "hallucination": False,
    }
