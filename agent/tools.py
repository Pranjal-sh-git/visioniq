"""Tool definitions for the VisionIQ Foundry Agent.

Wires existing implementations from services/ for multimodal product search,
catalog RAG knowledge retrieval, temporal video search, and product recommendations.
"""

import json
import logging
from pathlib import Path
import sys
from typing import Any, Optional, Union
from PIL import Image

# Ensure workspace root and backend are on sys.path
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
for directory in (str(ROOT_DIR), str(ROOT_DIR / "backend")):
    if directory not in sys.path:
        sys.path.insert(0, directory)

try:
    from backend.config import settings
except ImportError:
    from config import settings

from services.product_search.matcher import (
    identify_product as _identify_product,
    identify_product_by_text as _identify_product_by_text,
    find_similar_catalog_products as _find_similar_catalog_products,
    get_search_client,
)
from services.vision.open_world_identifier import identify_product_open_world
from services.rag.rag_service import (
    answer_product_question as _answer_product_question,
    retrieve_product_by_id,
)
from services.video.search import grounded_video_qa as _grounded_video_qa

logger = logging.getLogger(__name__)


def identify_product(
    image: Optional[Union[str, bytes, Path, Image.Image]] = None,
    image_url: Optional[str] = None,
    query: Optional[str] = None,
    top_k: int = 3,
) -> dict[str, Any]:
    """Identifies ANY product from an uploaded image or query description using Open-World Vision AI.

    Args:
        image: Local image file path, HTTP/HTTPS URL, raw image bytes, or PIL Image.
        image_url: Image URL if passed separately.
        query: Optional text description fallback.
        top_k: Number of top candidate matches to retrieve.

    Returns:
        dict[str, Any]: Identified product details, visual summary, and similar catalog recommendations.
    """
    target_img = image or image_url
    if target_img:
        # Step 1: Open-World Vision AI identification via gpt-5-mini
        open_world_info = identify_product_open_world(image=target_img, user_hint=query)

        # Step 2: Catalog recommendations via vector search
        similar_catalog = _find_similar_catalog_products(
            image=target_img,
            identified_info=open_world_info,
            top_k=top_k,
        )

        exact_match = next((item for item in similar_catalog if item.get("is_exact_catalog_match")), None)
        best_catalog = exact_match or (similar_catalog[0] if similar_catalog else None)

        prod_name = open_world_info.get("product_name", "Unidentified Product")
        brand = open_world_info.get("brand", "Unknown")
        visual_desc = open_world_info.get("visual_description", "")

        answer_summary = (
            f"I identified this product as **{prod_name}** ({brand}).\n\n"
            f"**Visual Analysis**: {visual_desc}\n"
        )
        if similar_catalog:
            rec_names = ", ".join([f"{c['brand']} {c['name']}" for c in similar_catalog[:2]])
            answer_summary += f"\n**Similar items in our catalog**: {rec_names}."

        return {
            "success": True,
            "answer": answer_summary,
            "identified_product": open_world_info,
            "identified_product_name": prod_name,
            "identified_product_id": best_catalog["id"] if best_catalog else None,
            "brand": brand,
            "category": open_world_info.get("category"),
            "similar_catalog_products": similar_catalog,
            "similar_products": similar_catalog,
            "best_match": best_catalog,
            "all_matches": similar_catalog,
            "is_confident": open_world_info.get("confidence") == "high",
        }

    elif query:
        matches = _identify_product_by_text(query_text=query, top_k=top_k)
        best_match = matches[0] if matches else None
        return {
            "success": True,
            "answer": f"Based on your query '{query}', the closest match is **{best_match['name']}**." if best_match else "No match found.",
            "best_match": best_match,
            "all_matches": matches,
            "similar_catalog_products": matches,
            "similar_products": matches,
            "identified_product_name": best_match["name"] if best_match else None,
            "identified_product_id": best_match["id"] if best_match else None,
            "is_confident": best_match.get("is_confident_match", False) if best_match else False,
        }
    else:
        return {
            "success": False,
            "error": "An image or text description is required to identify a product.",
            "matches": [],
            "similar_products": [],
        }


def search_product_knowledge(
    query: str,
    product_id: Optional[str] = None,
    product_name: Optional[str] = None,
) -> dict[str, Any]:
    """Searches catalog knowledge and specifications to answer product questions.

    Args:
        query (str): Question or query regarding product specifications, battery, weight, etc.
        product_id (Optional[str]): Target product ID (e.g. 'P001').
        product_name (Optional[str]): Target product name if product_id is not known.

    Returns:
        dict[str, Any]: Grounded catalog answer and specification data or clarification request.
    """
    target_pid = product_id

    # If product_id not directly provided, search by explicit product name if present
    if not target_pid and product_name:
        candidates = _identify_product_by_text(product_name, top_k=1)
        if candidates and candidates[0]["similarity_score"] >= 0.80:
            target_pid = candidates[0]["id"]

    # When no product_id is given or resolved, answer_product_question asks for clarification
    result = _answer_product_question(product_id=target_pid, question=query)
    return result


def search_video(
    video_id: str,
    query: str,
    top_k: int = 3,
) -> dict[str, Any]:
    """Searches within a video's timestamped segments for spoken words or topics.

    Args:
        video_id (str): Video identifier (e.g. 'vid_df16da8f30f96fb6').
        query (str): Question or description of the moment to retrieve.
        top_k (int): Number of candidate segments to evaluate.

    Returns:
        dict[str, Any]: Grounded answer with exact start_time, end_time, and supporting segment.
    """
    return _grounded_video_qa(video_id=video_id, question=query, top_k=top_k)


def find_similar_products(
    product_id: Optional[str] = None,
    image: Optional[Union[str, bytes, Path, Image.Image]] = None,
    image_url: Optional[str] = None,
    category: Optional[str] = None,
    top_k: int = 4,
) -> dict[str, Any]:
    """Finds visually or categorically similar products in the catalog.

    Args:
        product_id (Optional[str]): Source product ID to find alternatives for.
        image: Source image to find visual matches for.
        image_url: Source image URL.
        category (Optional[str]): Filter by category (e.g. 'Headphones', 'Chairs').
        top_k (int): Number of similar products to return.

    Returns:
        dict[str, Any]: List of similar products with similarity scores and specs.
    """
    target_img = image or image_url

    if target_img:
        matches = _identify_product(image=target_img, top_k=top_k + 1)
        similar = [m for m in matches if m.get("id") != product_id][:top_k]
        return {
            "source_product_id": product_id,
            "similar_products": similar,
            "count": len(similar),
        }

    if product_id:
        source_doc = retrieve_product_by_id(product_id)
        if source_doc:
            prod_category = category or source_doc.get("category")
            prod_name = source_doc.get("name", "")
            # Query text matching in same category
            matches = _identify_product_by_text(f"{prod_category} {prod_name}", top_k=top_k + 2)
            similar = [m for m in matches if m.get("id") != product_id][:top_k]
            return {
                "source_product_id": product_id,
                "source_product_name": prod_name,
                "category": prod_category,
                "similar_products": similar,
                "count": len(similar),
            }

    # Fallback to category search or general catalog
    query_text = category or "Headphones"
    matches = _identify_product_by_text(query_text, top_k=top_k)
    return {
        "source_product_id": product_id,
        "category": category,
        "similar_products": matches[:top_k],
        "count": len(matches[:top_k]),
    }
