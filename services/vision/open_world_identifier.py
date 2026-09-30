"""Open-World Multimodal Product Identification Service.

Uses Azure OpenAI (gpt-5-mini) with multimodal vision capabilities to accurately
recognize brands, models, categories, and visual features from ANY uploaded image,
free from closed-set catalog constraints.

Optimized for minimal token usage by resizing/compressing images to max 512px
and generating concise product identification metadata.
"""

import base64
import io
import json
import logging
from pathlib import Path
import sys
from typing import Any, Optional, Union
import urllib.request
from PIL import Image

# Ensure workspace root and backend are on sys.path
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent.parent
for directory in (str(ROOT_DIR), str(ROOT_DIR / "backend")):
    if directory not in sys.path:
        sys.path.insert(0, directory)

try:
    from backend.config import settings
except ImportError:
    from config import settings

from services.llm import get_azure_openai_client

logger = logging.getLogger("visioniq.vision.open_world")

# Maximum dimension (width/height) for vision LLM inference to minimize vision tokens
MAX_VISION_IMAGE_SIZE = 512


def _resize_and_compress_image(pil_img: Image.Image, max_dim: int = MAX_VISION_IMAGE_SIZE) -> str:
    """Resizes image to max_dim on the longest side and compresses to JPEG base64 data URI."""
    if pil_img.mode in ("RGBA", "LA", "P"):
        rgb_img = Image.new("RGB", pil_img.size, (255, 255, 255))
        if pil_img.mode == "P":
            pil_img = pil_img.convert("RGBA")
        rgb_img.paste(pil_img, mask=pil_img.split()[-1] if len(pil_img.split()) == 4 else None)
        pil_img = rgb_img
    elif pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")

    # Resize to max 512px on longest side preserving aspect ratio
    if max(pil_img.width, pil_img.height) > max_dim:
        pil_img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

    buffered = io.BytesIO()
    pil_img.save(buffered, format="JPEG", quality=85, optimize=True)
    b64_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64_str}"


def _image_to_data_uri(image: Union[str, bytes, Path, Image.Image]) -> str:
    """Loads, resizes (max 512px), and converts image input into a compact base64 JPEG data URI."""
    if isinstance(image, str):
        if image.startswith("data:image/"):
            return image
        if image.startswith("http://") or image.startswith("https://"):
            from services.security import safe_fetch_image
            raw_bytes = safe_fetch_image(image)
            pil_img = Image.open(io.BytesIO(raw_bytes))
            return _resize_and_compress_image(pil_img)

        image_path = Path(image)
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image}")
        pil_img = Image.open(image_path)
        return _resize_and_compress_image(pil_img)

    elif isinstance(image, Path):
        if not image.exists():
            raise FileNotFoundError(f"Image file not found: {image}")
        pil_img = Image.open(image)
        return _resize_and_compress_image(pil_img)

    elif isinstance(image, bytes):
        pil_img = Image.open(io.BytesIO(image))
        return _resize_and_compress_image(pil_img)

    elif isinstance(image, Image.Image):
        return _resize_and_compress_image(image)

    raise ValueError(f"Unsupported image input type: {type(image)}")


def identify_product_open_world(
    image: Optional[Union[str, bytes, Path, Image.Image]] = None,
    image_url: Optional[str] = None,
    user_hint: Optional[str] = None,
) -> dict[str, Any]:
    """Identifies ANY product in the world from an image using Azure OpenAI gpt-5-mini vision.

    Optimized for token efficiency: image is compressed to max 512px and prompt produces
    a concise JSON response.

    Args:
        image: Local image file path, raw bytes, Path, or PIL Image.
        image_url: Remote image URL or data URI.
        user_hint: Optional text context or query provided by the user.

    Returns:
        dict[str, Any]: Structured open-world identification details including
                        brand, model, category, product_name, visual_description,
                        confidence, and key_features_observed.
    """
    target = image or image_url
    if not target:
        raise ValueError("Either an image or image_url must be provided.")

    data_uri = _image_to_data_uri(target)
    client = get_azure_openai_client()
    deployment = settings.AZURE_OPENAI_DEPLOYMENT_NAME

    system_instruction = (
        "You are VisionIQ's Universal Multimodal Product & Media Intelligence Specialist.\n"
        "Your task is to identify ANY commercial product, book, publication, packaged grocery item, cosmetic, "
        "piece of apparel, footwear, gadget, furniture, tool, artwork, or consumer good from the provided image.\n\n"
        "UNIVERSAL RECOGNITION RULES:\n"
        "1. VISUAL OCR & BRAND RECOGNITION: Always read prominent printed text, author names, packaging labels, and brand logos.\n"
        "2. ICONIC DESIGN & SILHOUETTE RECOGNITION: Identify well-known products and electronics by their iconic industrial design, "
        "ear cup/headband curvature, mesh weave, frame contours, button layout, outsole silhouette, and distinctive styling "
        "(e.g. Sony WH-1000XM5 / WH-1000XM4, Bose QuietComfort 45 / Ultra, Apple AirPods Max, Herman Miller Aeron / Embody, "
        "Nike Air Zoom Pegasus, Rolex Submariner, etc.). If you recognize the distinctive model and manufacturer, specify the actual "
        "brand (e.g. 'Sony') and model (e.g. 'Sony WH-1000XM5') with high or medium confidence rather than marking brand as 'Unknown'.\n"
        "3. ENTITY MAPPING:\n"
        "   - Books / Publications: 'brand' = Author or Publisher (e.g. 'Robert T. Kiyosaki'), 'model' = Edition/Sub-title, 'product_name' = Book Title (e.g. 'Rich Dad Poor Dad'), 'category' = 'Books & Publications'.\n"
        "   - Groceries / Packaged Goods: 'brand' = Brand/Manufacturer, 'product_name' = Item Name & Flavor/Variant, 'category' = 'Groceries & Food'.\n"
        "   - Cosmetics / Personal Care: 'brand' = Brand, 'product_name' = Product Line / Formula, 'category' = 'Personal Care & Beauty'.\n"
        "   - Electronics & Gadgets / Audio: 'brand' = Manufacturer (e.g. 'Sony', 'Bose', 'Apple'), 'model' = Model name (e.g. 'WH-1000XM5'), 'product_name' = Full name (e.g. 'Sony WH-1000XM5'), 'category' = 'Headphones' or 'Electronics & Gadgets' or 'Watches'.\n"
        "   - Footwear & Apparel: 'brand' = Brand/Label (e.g. 'Nike'), 'model' = Silhouette/Style (e.g. 'Air Zoom Pegasus'), 'category' = 'Shoes' or 'Apparel'.\n"
        "   - Furniture & Home: 'brand' = Brand or Maker (e.g. 'Herman Miller'), 'product_name' = Descriptive Item Name (e.g. 'Herman Miller Aeron Chair'), 'category' = 'Chairs' or 'Home & Furniture'.\n"
        "   - General / Other: State the clear descriptive name (e.g., 'Stainless Steel Water Bottle').\n"
        "4. CONFIDENCE & HEDGING:\n"
        "   - Set confidence = 'high' when title/brand/model is recognized from text or iconic industrial design.\n"
        "   - Set confidence = 'medium' when the product category and general brand are known but exact variant is uncertain.\n"
        "   - Set confidence = 'low' only if the image is extremely blurry or completely unidentifiable.\n\n"
        "You MUST respond ONLY with a valid JSON object matching the requested schema."
    )

    prompt_text = (
        "Identify this item completely (reading all visible text, distinctive silhouette/model design, author/brand, and packaging details).\n"
        "Keep the visual description concise (1-2 sentences) and list up to 4 key observed physical features.\n"
    )
    if user_hint:
        prompt_text += f"User hint: '{user_hint}'\n"

    prompt_text += (
        "\nJSON schema:\n"
        "{\n"
        '  "brand": "Brand, Manufacturer, Author, or Maker name (e.g. Sony, Nike, Herman Miller, Apple, or Unknown if unidentifiable)",\n'
        '  "model": "Model, Edition, Style, or Variant (e.g. WH-1000XM5, Air Zoom Pegasus)",\n'
        '  "product_name": "Full recognizable title or product name (e.g. Sony WH-1000XM5)",\n'
        '  "category": "Books & Publications | Electronics & Gadgets | Headphones | Chairs | Shoes | Watches | Groceries & Food | Personal Care & Beauty | Apparel | Home & Furniture | Other",\n'
        '  "visual_description": "Concise 1-2 sentence visual summary highlighting key colors, materials, text, or format",\n'
        '  "confidence": "high | medium | low",\n'
        '  "key_features_observed": ["List of up to 4 key observed physical features"]\n'
        "}"
    )

    try:
        logger.info(f"[OPEN-WORLD IDENTIFY] Sending 512px-compressed image to Azure OpenAI ({deployment})...")
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": system_instruction},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                },
            ],
            max_completion_tokens=800,  # Covers reasoning tokens + concise JSON tokens
            response_format={"type": "json_object"},
        )

        raw_content = response.choices[0].message.content or "{}"
        parsed = json.loads(raw_content)

        brand = parsed.get("brand") or "Unknown"
        model = parsed.get("model") or ""
        product_name = parsed.get("product_name") or f"{brand} {model}".strip() or "Unidentified Product"
        category = parsed.get("category") or "General"
        visual_desc = parsed.get("visual_description") or ""
        confidence = str(parsed.get("confidence", "medium")).lower()
        if confidence not in ("high", "medium", "low"):
            confidence = "medium"
        features = parsed.get("key_features_observed") or []
        if not isinstance(features, list):
            features = [str(features)]

        result = {
            "brand": brand,
            "model": model,
            "product_name": product_name,
            "category": category,
            "visual_description": visual_desc,
            "confidence": confidence,
            "key_features_observed": features[:4],
            "is_open_world": True,
        }

        logger.info(
            f"[OPEN-WORLD IDENTIFY] Product identified: '{product_name}' "
            f"(Brand: {brand}, Category: {category}, Confidence: {confidence})"
        )
        return result

    except Exception as e:
        logger.error(f"[OPEN-WORLD IDENTIFY ERROR] Vision LLM identification failed: {e}")
        return {
            "brand": "Unknown",
            "model": "Unspecified",
            "product_name": "Unidentified Product",
            "category": "General",
            "visual_description": f"Could not perform visual recognition: {str(e)}",
            "confidence": "low",
            "key_features_observed": [],
            "is_open_world": True,
            "error": str(e),
        }
