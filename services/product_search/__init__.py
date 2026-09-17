"""Product search and visual identification service module."""

from services.product_search.embeddings import (
    generate_image_embedding,
    generate_text_embedding,
)
from services.product_search.matcher import (
    identify_product,
    identify_product_by_text,
)

__all__ = [
    "generate_image_embedding",
    "generate_text_embedding",
    "identify_product",
    "identify_product_by_text",
]
