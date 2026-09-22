"""RAG Service for Product Catalog Knowledge Retrieval and Answering.

Queries Azure AI Search for grounded product context and provides intelligent,
conversational, and grounded answers using Azure OpenAI foundation models.
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

from services.llm import generate_grounded_answer

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


def answer_product_question(
    product_id: Optional[str],
    question: str,
    product_info: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Answers natural language questions about a product, grounded in catalog specifications or open-world vision data.

    Provides rich, conversational, and factual answers synthesized by Azure OpenAI (gpt-5-mini),
    while preserving strict honesty when requested information is unlisted.

    Returns:
        dict: Contains answer, grounded_field, catalog_value, and is_available flag.
    """
    if not product_id and not product_info:
        return {
            "product_id": None,
            "question": question,
            "answer": "Which product are you asking about? Please specify the product name or ID.",
            "requires_clarification": True,
            "is_available": False,
            "grounded_field": None,
            "catalog_value": None,
        }

    # Case 1: Catalog lookup by product_id if provided
    product = retrieve_product_by_id(product_id) if product_id else None

    # Case 2: Open-world identified product info (used if product not in catalog or product_id is None)
    if not product and product_info:
        name = product_info.get("product_name") or product_info.get("model", "Identified Product")
        brand = product_info.get("brand", "")
        category = product_info.get("category", "")
        description = product_info.get("visual_description", "")
        features = product_info.get("key_features_observed") or product_info.get("features", [])
        specs = product_info.get("specifications", {})

        display_name = name if (brand and name.lower().startswith(brand.lower())) else f"{brand} {name}".strip()
        features_formatted = "\n".join(f"- {f}" for f in features) if features else "None listed"
        specs_formatted = "\n".join(f"- {k.replace('_', ' ').title()}: {v}" for k, v in specs.items()) if specs else "None listed"

        context_str = (
            f"Product: {display_name}\n"
            f"Brand: {brand}\n"
            f"Category: {category}\n"
            f"Visual Observations & Description: {description}\n\n"
            f"Observed Features & Attributes:\n{features_formatted}\n\n"
            f"Technical Specifications:\n{specs_formatted}"
        )

        system_instruction = (
            f"You are VisionIQ's AI Specialist for {display_name}.\n"
            f"Your goal is to answer the user's natural language question in a helpful, friendly, conversational, "
            f"and accurate manner based on the visual identification context and general knowledge of this product/book/item.\n\n"
            f"Guidelines:\n"
            f"1. Conversational & Informative: Speak naturally in complete, well-formed sentences. "
            f"Explain observed features, book summary/themes, author background, usage, or physical characteristics with rich context.\n"
            f"2. Domain-Aware Explanations: Tailor your response to the category (e.g., synopsis, lessons, and edition details for books; ingredients/usage for cosmetics & groceries; ergonomics and fit for shoes/chairs; specs for electronics).\n"
            f"3. Visual Grounding: When asked about visual features, reference the observed cover, format, colors, or packaging.\n"
            f"4. Honesty on Live Data: If asked for real-time live checkout links or local store stock not in the system, clearly state that direct purchasing links are not in the profile."
        )

        llm_answer = generate_grounded_answer(
            user_question=question,
            retrieved_context=context_str,
            system_instruction=system_instruction,
        )

        is_missing_info = (
            "not specified" in llm_answer.lower()
            or "not mentioned" in llm_answer.lower()
            or "does not specify" in llm_answer.lower()
        )

        return {
            "product_id": None,
            "product_name": display_name,
            "question": question,
            "answer": llm_answer,
            "requires_clarification": False,
            "is_available": not is_missing_info,
            "grounded_field": None,
            "catalog_value": None,
            "hallucination": False,
        }

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
    category = product.get("category", "")
    specs = product.get("specifications", {})
    description = product.get("description", "")
    features = product.get("features", [])

    # Avoid duplicate brand name prefix if name already contains it
    display_name = name if name.lower().startswith(brand.lower()) else f"{brand} {name}".strip()

    # Format structured catalog specifications and features for LLM context
    specs_formatted = "\n".join(f"- {k.replace('_', ' ').title()}: {v}" for k, v in specs.items()) if specs else "None listed"
    features_formatted = "\n".join(f"- {f}" for f in features) if features else "None listed"

    context_str = (
        f"Product: {display_name} (ID: {product_id})\n"
        f"Brand: {brand}\n"
        f"Category: {category}\n"
        f"Description: {description}\n\n"
        f"Key Features:\n{features_formatted}\n\n"
        f"Technical Specifications:\n{specs_formatted}"
    )

    # Identify if a specific known spec field is targeted (for telemetry / metadata)
    q_lower = question.lower()
    matched_field = None
    matched_value = None

    field_synonyms = {
        "charging": ["charging", "charge", "charged", "charger", "fast charging", "port"],
        "connectivity": ["connectivity", "connect", "connection", "bluetooth", "aux", "wireless", "wired"],
        "battery_life": ["battery", "battery life", "battery_life", "run time", "runtime", "playback"],
        "driver_size": ["driver", "driver size", "driver_size", "drivers", "transducer", "speaker size"],
        "noise_cancellation": ["noise cancellation", "noise cancelling", "anc", "noise_cancellation", "noise cancel"],
        "weight": ["weight", "weigh", "heavy", "mass", "grams", "lbs"],
        "material": ["material", "materials", "leather", "fabric", "aluminum", "mesh"],
        "adjustments": ["adjustments", "adjust", "armrests", "lumbar", "recline", "tilt"],
        "warranty": ["warranty", "guarantee"],
    }

    for key, val in specs.items():
        key_normalized = key.replace("_", " ").lower()
        synonyms = field_synonyms.get(key, [key_normalized])
        if key_normalized in q_lower or any(syn in q_lower for syn in synonyms):
            matched_field = key
            matched_value = val
            break

    system_instruction = (
        f"You are VisionIQ's AI Product Specialist for {display_name}.\n"
        f"Your goal is to answer the user's natural language question in a helpful, friendly, conversational, "
        f"and accurate manner based strictly on the provided catalog data.\n\n"
        f"Guidelines:\n"
        f"1. Conversational & Informative: Speak naturally in complete, well-formed sentences. "
        f"Explain specs and features with useful context rather than just stating isolated numbers.\n"
        f"2. Factual Accuracy: For specific metrics (e.g. battery life, weight, driver size, warranty, material), "
        f"always include the exact values from the catalog.\n"
        f"3. Practical Insights: For broader questions (e.g. suitability for travel, comfort, fitness, sound quality), "
        f"synthesize an informed answer from the product's verified description, features, and specifications.\n"
        f"4. Honesty on Missing Info: If the user asks about a specific feature that is completely unlisted or not present in the catalog data (e.g. an unlisted waterproof rating or unlisted accessory), "
        f"clearly state that this specific detail is not specified in the catalog for {display_name}."
    )

    llm_answer = generate_grounded_answer(
        user_question=question,
        retrieved_context=context_str,
        system_instruction=system_instruction,
    )

    # Determine if response is answering from available catalog data
    is_missing_info = (
        "not specified in the product catalog" in llm_answer.lower()
        or "not mentioned in the catalog" in llm_answer.lower()
        or "is not specified" in llm_answer.lower()
        or "does not specify" in llm_answer.lower()
    )

    return {
        "product_id": product_id,
        "product_name": name,
        "question": question,
        "answer": llm_answer,
        "requires_clarification": False,
        "is_available": not is_missing_info,
        "grounded_field": matched_field,
        "catalog_value": matched_value,
        "hallucination": False,
    }
