"""Product identification and catalog retrieval API route definitions."""

import logging
from pathlib import Path
import shutil
from typing import Any, Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from services.product_search.matcher import (
    identify_product as _identify_product,
    identify_product_by_text as _identify_product_by_text,
    find_similar_catalog_products as _find_similar_catalog_products,
)
from services.vision.open_world_identifier import identify_product_open_world
from services.rag.rag_service import retrieve_product_by_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/product", tags=["Product Intelligence"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "uploads" / "images"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class TextIdentifyRequest(BaseModel):
    query: str = Field(..., description="Text query describing the product.")
    top_k: int = Field(3, description="Number of top matching candidate products.")
    confidence_threshold: float = Field(0.85, description="Minimum confidence threshold.")


@router.post("/identify")
async def identify_product_endpoint(
    file: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    query: Optional[str] = Form(None),
    top_k: int = Form(3),
    confidence_threshold: float = Form(0.85),
):
    """Identifies products via Open-World Vision AI (gpt-5-mini) and suggests similar catalog items."""
    try:
        identified_product: Optional[dict[str, Any]] = None
        similar_catalog: list[dict[str, Any]] = []

        if file is not None:
            file_path = UPLOAD_DIR / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Step 1: Open-world vision identification via gpt-5-mini
            identified_product = identify_product_open_world(image=file_path)

            # Step 2: Separate catalog search for similar recommendations
            similar_catalog = _find_similar_catalog_products(
                image=file_path,
                identified_info=identified_product,
                top_k=top_k,
                confidence_threshold=confidence_threshold,
            )

        elif image_url:
            # Step 1: Open-world vision identification via gpt-5-mini
            identified_product = identify_product_open_world(image_url=image_url)

            # Step 2: Separate catalog search for similar recommendations
            similar_catalog = _find_similar_catalog_products(
                image=image_url,
                identified_info=identified_product,
                top_k=top_k,
                confidence_threshold=confidence_threshold,
            )

        elif query:
            # For pure text queries, run text vector search
            matches = _identify_product_by_text(
                query_text=query,
                top_k=top_k,
                confidence_threshold=confidence_threshold,
            )
            similar_catalog = matches
            identified_product = {
                "brand": matches[0]["brand"] if matches else "Unknown",
                "model": matches[0]["name"] if matches else query,
                "product_name": matches[0]["name"] if matches else query,
                "category": matches[0]["category"] if matches else "General",
                "visual_description": f"Identified via text search query: '{query}'",
                "confidence": "high" if (matches and matches[0]["is_confident_match"]) else "medium",
                "key_features_observed": matches[0].get("features", []) if matches else [],
                "is_open_world": False,
            }

        else:
            raise HTTPException(
                status_code=400,
                detail="Either an image file, image_url, or query text must be provided.",
            )

        # Determine exact or strongest catalog match
        exact_catalog_match = next((item for item in similar_catalog if item.get("is_exact_catalog_match")), None)
        best_catalog_item = exact_catalog_match or (similar_catalog[0] if similar_catalog else None)
        is_confident = best_catalog_item.get("is_confident_match", False) if best_catalog_item else False

        return {
            "success": True,
            "identified_product": identified_product,
            "similar_catalog_products": similar_catalog,
            "catalog_match": exact_catalog_match or (best_catalog_item if is_confident else None),
            # Backwards compatibility fields for existing frontend & tests
            "best_match": best_catalog_item,
            "all_matches": similar_catalog,
            "is_confident_match": is_confident,
            "count": len(similar_catalog),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error during product identification")
        raise HTTPException(status_code=500, detail=f"Product identification failed: {str(e)}")


@router.get("/{product_id}")
async def get_product_by_id_endpoint(product_id: str):
    """Retrieves full specifications and metadata for a catalog product."""
    try:
        product = retrieve_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found.")
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving product {product_id}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve product: {str(e)}")
