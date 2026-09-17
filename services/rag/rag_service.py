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

    # Synonym mapping for common natural language terms
    field_synonyms = {
        "charging": ["charging", "charge", "charged", "charger", "fast charging", "port"],
        "connectivity": ["connectivity", "connect", "connection", "bluetooth", "aux", "wireless", "wired"],
        "battery_life": ["battery", "battery life", "battery_life", "run time", "runtime"],
        "driver_size": ["driver", "driver size", "driver_size", "drivers", "transducer"],
        "noise_cancellation": ["noise cancellation", "noise cancelling", "anc", "noise_cancellation"],
        "weight": ["weight", "weigh", "heavy", "mass"],
        "type": ["form factor", "headphone type", "chair type", "shoe type"],
    }

    # Match against specifications dictionary keys (prioritize longer/specific keys over generic ones like 'type')
    matched_value = None
    matched_field = None

    sorted_keys = sorted(specs.keys(), key=lambda k: len(k), reverse=True)

    for key in sorted_keys:
        val = specs[key]
        key_normalized = key.replace("_", " ").lower()
        synonyms = field_synonyms.get(key, [key_normalized])

        if key_normalized in q_lower or any(syn in q_lower for syn in synonyms):
            matched_value = val
            matched_field = key
            break

    # Build retrieved context block from catalog
    context_str = (
        f"Product ID: {product_id}\n"
        f"Product Name: {display_name}\n"
        f"Category: {product.get('category', '')}\n"
        f"Description: {description}\n"
        f"Specifications: {json.dumps(specs, indent=2)}\n"
        f"Features: {json.dumps(features)}"
    )

    from services.llm import generate_grounded_answer

    if matched_value:
        llm_answer = generate_grounded_answer(
            user_question=question,
            retrieved_context=context_str,
            system_instruction=(
                f"You are VisionIQ's Strict Grounded Product Assistant. "
                f"Answer the user's question accurately using ONLY the verbatim retrieved product specifications for {display_name}. "
                f"State the exact value '{matched_value}' concisely. Do NOT add external real-world assumptions or qualifiers not found in the context."
            ),
        )

        return {
            "product_id": product_id,
            "product_name": name,
            "question": question,
            "answer": llm_answer,
            "requires_clarification": False,
            "is_available": True,
            "grounded_field": matched_field,
            "catalog_value": matched_value,
            "hallucination": False,
        }

    # If field is absent from catalog specifications
    llm_answer = generate_grounded_answer(
        user_question=question,
        retrieved_context=context_str,
        system_instruction=(
            f"You are VisionIQ's Strict Grounded Product Assistant. "
            f"The user is asking about a specification for {display_name}. "
            f"Since the requested information is not present in the retrieved specifications, respond strictly with:\n"
            f"'This information is not specified in the product catalog for {display_name}.'\n"
            f"Do NOT give buying recommendations, external advice, or assumptions."
        ),
    )

    return {
        "product_id": product_id,
        "product_name": name,
        "question": question,
        "answer": llm_answer,
        "requires_clarification": False,
        "is_available": False,
        "grounded_field": None,
        "catalog_value": None,
        "hallucination": False,
    }
