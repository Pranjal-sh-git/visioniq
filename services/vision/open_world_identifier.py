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
            try:
                req = urllib.request.Request(image, headers={"User-Agent": "VisionIQ/1.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    pil_img = Image.open(io.BytesIO(resp.read()))
                    return _resize_and_compress_image(pil_img)
            except Exception as e:
                logger.warning(f"Failed to fetch and compress remote image URL: {e}. Falling back to URL string.")
                return image

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
        "You are VisionIQ's Open-World Multimodal Product Intelligence Specialist.\n"
        "Identify the commercial product in the image. Be concise, honest, and accurate.\n\n"
        "CRITICAL MODEL IDENTIFICATION RULE:\n"
        "If you are not highly confident about the EXACT model number, say so clearly "
        "(e.g. 'Sony brand, WH-series headphones, exact model uncertain') rather than stating a specific "
        "model number that may be a guess. Brand and category identification should be confident; exact model number "
        "identification should be hedged unless very clearly visible (e.g. from text/logo in the image).\n\n"
        "You MUST respond ONLY with a valid JSON object matching the requested schema."
    )

    prompt_text = (
        "Identify this product: brand, model, and category.\n"
        "If the exact model number is not explicitly visible or certain, state the model as uncertain/hedged (e.g. 'WH-series, exact model uncertain').\n"
        "Keep the visual description concise (1-2 sentences) and list max 4 key observed features.\n"
    )
    if user_hint:
        prompt_text += f"User hint: '{user_hint}'\n"

    prompt_text += (
        "\nJSON schema:\n"
        "{\n"
        '  "brand": "Brand name or Unknown",\n'
        '  "model": "Model name / series or Unknown",\n'
        '  "product_name": "Short descriptive product name",\n'
        '  "category": "Headphones | Chairs | Shoes | Watches | Electronics | Apparel | Other",\n'
        '  "visual_description": "Concise 1-2 sentence visual summary",\n'
        '  "confidence": "high | medium | low",\n'
        '  "key_features_observed": ["List of up to 4 key physical features"]\n'
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
            max_completion_tokens=800,  # Covers ~500 reasoning tokens + 100-150 concise JSON tokens
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
