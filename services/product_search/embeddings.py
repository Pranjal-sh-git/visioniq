"""Product Image Embedding Service.

Model Used: OpenAI CLIP (ViT-B/32) / `clip-ViT-B-32`
Why this model:
- Architecture: Vision Transformer (ViT-B/32) trained contrastively with a text transformer
  on 400M (image, text) pairs.
- Shared Embedding Space: Embeds images and text descriptions into the exact same 512-dimensional
  vector space, enabling both zero-shot visual similarity and text-to-image / cross-modal search.
- Product Identification: Captures high-level semantic features, object geometries, branding,
  color palettes, and structural characteristics without requiring domain-specific fine-tuning.
- Efficiency: Generates normalized 512-dim vectors optimized for high-throughput cosine similarity
  search in Azure AI Search (HNSW index).
"""

from io import BytesIO
import logging
from pathlib import Path
from typing import Any, Union
import numpy as np
from PIL import Image
import requests

logger = logging.getLogger(__name__)

# Global model cache to avoid re-loading weights on every call
_EMBEDDING_MODEL = None
EMBEDDING_DIM = 512
MODEL_NAME = "clip-ViT-B-32"


def get_embedding_model():
    """Lazy-loads and returns the CLIP image embedding model."""
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading image embedding model: {MODEL_NAME}")
            _EMBEDDING_MODEL = SentenceTransformer(MODEL_NAME)
        except ImportError:
            try:
                from transformers import CLIPModel, CLIPProcessor
                logger.info(f"Loading transformers CLIP model: openai/{MODEL_NAME}")
                processor = CLIPProcessor.from_pretrained(f"openai/{MODEL_NAME}")
                model = CLIPModel.from_pretrained(f"openai/{MODEL_NAME}")
                _EMBEDDING_MODEL = (model, processor)
            except Exception as e:
                raise RuntimeError(
                    f"Failed to load CLIP embedding model. Ensure `sentence-transformers` or `transformers` and `torch` are installed: {e}"
                )
    return _EMBEDDING_MODEL


def load_image(image_input: Union[str, bytes, Path, Image.Image]) -> Image.Image:
    """Loads an image from various input types into a RGB PIL Image.

    Args:
        image_input: Can be a local file path, URL string, raw bytes, or PIL Image.

    Returns:
        Image.Image: RGB PIL Image object.
    """
    if isinstance(image_input, Image.Image):
        return image_input.convert("RGB")

    if isinstance(image_input, (str, Path)):
        image_path_str = str(image_input)
        if image_path_str.startswith(("http://", "https://")):
            response = requests.get(image_path_str, timeout=15)
            response.raise_for_status()
            return Image.open(BytesIO(response.content)).convert("RGB")
        else:
            return Image.open(image_path_str).convert("RGB")

    if isinstance(image_input, (bytes, bytearray)):
        return Image.open(BytesIO(image_input)).convert("RGB")

    raise ValueError(f"Unsupported image input type: {type(image_input)}")


def generate_image_embedding(image_input: Union[str, bytes, Path, Image.Image]) -> list[float]:
    """Generates a normalized 512-dimensional vector embedding for an image.

    Args:
        image_input: Local file path, URL, raw bytes, or PIL Image.

    Returns:
        list[float]: 512-dimensional embedding vector as float list.
    """
    img = load_image(image_input)
    model_obj = get_embedding_model()

    # SentenceTransformer format
    if hasattr(model_obj, "encode"):
        embedding = model_obj.encode(img, convert_to_numpy=True, normalize_embeddings=True)
        return embedding.tolist()

    # Transformers CLIP format
    import torch
    model, processor = model_obj
    inputs = processor(images=img, return_tensors="pt")
    with torch.no_grad():
        image_features = model.get_image_features(**inputs)
        # Normalize to unit length for cosine similarity
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        return image_features[0].cpu().numpy().tolist()


def generate_text_embedding(text: str) -> list[float]:
    """Generates a normalized 512-dimensional vector embedding for a text query using CLIP.

    Args:
        text (str): Query or product description text.

    Returns:
        list[float]: 512-dimensional embedding vector in the same space as images.
    """
    model_obj = get_embedding_model()

    if hasattr(model_obj, "encode"):
        embedding = model_obj.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return embedding.tolist()

    import torch
    model, processor = model_obj
    inputs = processor(text=[text], return_tensors="pt", padding=True)
    with torch.no_grad():
        text_features = model.get_text_features(**inputs)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        return text_features[0].cpu().numpy().tolist()
