"""Text Retrieval Embedding Service for Video Transcripts and RAG.

Model Used: sentence-transformers/all-MiniLM-L6-v2 (384-dimensional dense vectors)
Why this model:
- Specifically fine-tuned on 1B+ semantic search, QA, and passage retrieval pairs (MS MARCO, SNLI, SQuAD).
- Unlike multimodal CLIP (which is designed for image-caption matching and suffers length distortion
  on conversational transcripts), all-MiniLM-L6-v2 provides state-of-the-art dense semantic text
  similarity for question-to-transcript retrieval.
- Normalized 384-dim embeddings provide fast, accurate cosine distance calculations in Azure AI Search.
"""

import logging
from typing import Union
import numpy as np

logger = logging.getLogger(__name__)

_TEXT_RETRIEVAL_MODEL = None
TEXT_EMBEDDING_DIM = 384
TEXT_MODEL_NAME = "all-MiniLM-L6-v2"


def get_text_retrieval_model():
    """Lazy-loads and returns the all-MiniLM-L6-v2 text embedding model."""
    global _TEXT_RETRIEVAL_MODEL
    if _TEXT_RETRIEVAL_MODEL is None:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading dense text retrieval model: {TEXT_MODEL_NAME}")
        _TEXT_RETRIEVAL_MODEL = SentenceTransformer(TEXT_MODEL_NAME)
    return _TEXT_RETRIEVAL_MODEL


def generate_transcript_embedding(text: str) -> list[float]:
    """Generates a normalized 384-dimensional semantic embedding for transcript chunks and queries.

    Args:
        text (str): Query or transcript chunk text.

    Returns:
        list[float]: Normalized 384-dimensional float vector.
    """
    model = get_text_retrieval_model()
    embedding = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
    return embedding.tolist()
