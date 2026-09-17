"""Video RAG and Semantic Temporal Search Service.

Provisions the "video-segments" vector index in Azure AI Search, indexes
timestamped video chunks, executes semantic temporal search filtered by video_id,
and generates grounded answers with exact start/end timestamps and video summaries.
"""

import json
import logging
from pathlib import Path
import sys
from typing import Any, Optional
import numpy as np

# Ensure workspace root and backend are on sys.path
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent.parent
for directory in (str(ROOT_DIR), str(ROOT_DIR / "backend")):
    if directory not in sys.path:
        sys.path.insert(0, directory)

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SearchableField,
    SimpleField,
    VectorSearch,
    VectorSearchAlgorithmMetric,
    VectorSearchProfile,
)
from azure.search.documents.models import VectorizedQuery

try:
    from backend.config import settings
except ImportError:
    from config import settings

from services.video.embeddings import (
    TEXT_EMBEDDING_DIM as EMBEDDING_DIM,
    generate_transcript_embedding,
)

logger = logging.getLogger(__name__)

VIDEO_INDEX_NAME = "video-segments"
VECTOR_PROFILE_NAME = "video-vector-profile"
ALGORITHM_CONFIG_NAME = "video-hnsw-config"
CACHE_DIR = ROOT_DIR / "data" / "cache" / "video_analysis"

VIDEO_CONFIDENCE_THRESHOLD = 0.65


def get_search_index_client() -> SearchIndexClient:
    """Instantiates SearchIndexClient from config."""
    return SearchIndexClient(
        endpoint=settings.AZURE_SEARCH_ENDPOINT,
        credential=AzureKeyCredential(settings.AZURE_SEARCH_KEY),
    )


def get_video_search_client() -> SearchClient:
    """Instantiates SearchClient for the video-segments index."""
    return SearchClient(
        endpoint=settings.AZURE_SEARCH_ENDPOINT,
        index_name=VIDEO_INDEX_NAME,
        credential=AzureKeyCredential(settings.AZURE_SEARCH_KEY),
    )


def ensure_video_segments_index() -> SearchIndex:
    """Provisions or updates the 'video-segments' vector index in Azure AI Search."""
    index_client = get_search_index_client()

    fields = [
        SimpleField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,
            filterable=True,
            sortable=True,
        ),
        SimpleField(
            name="video_id",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True,
        ),
        SimpleField(
            name="start_time",
            type=SearchFieldDataType.Double,
            filterable=True,
            sortable=True,
        ),
        SimpleField(
            name="end_time",
            type=SearchFieldDataType.Double,
            filterable=True,
            sortable=True,
        ),
        SearchableField(
            name="topic",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SearchableField(
            name="transcript",
            type=SearchFieldDataType.String,
        ),
        SearchField(
            name="embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=EMBEDDING_DIM,
            vector_search_profile_name=VECTOR_PROFILE_NAME,
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name=ALGORITHM_CONFIG_NAME,
                parameters=HnswParameters(metric=VectorSearchAlgorithmMetric.COSINE),
            )
        ],
        profiles=[
            VectorSearchProfile(
                name=VECTOR_PROFILE_NAME,
                algorithm_configuration_name=ALGORITHM_CONFIG_NAME,
            )
        ],
    )

    index = SearchIndex(name=VIDEO_INDEX_NAME, fields=fields, vector_search=vector_search)
    return index_client.create_or_update_index(index)


def index_video_chunks_to_search(video_id: str, chunks: list[dict[str, Any]]) -> int:
    """Indexes timestamped chunks of a video into Azure AI Search."""
    if not chunks:
        return 0

    ensure_video_segments_index()
    search_client = get_video_search_client()

    docs = []
    for idx, chunk in enumerate(chunks):
        doc_id = f"{video_id}_{idx}"
        docs.append({
            "id": doc_id,
            "video_id": video_id,
            "start_time": float(chunk.get("start_time", 0.0)),
            "end_time": float(chunk.get("end_time", 0.0)),
            "topic": chunk.get("topic", ""),
            "transcript": chunk.get("transcript", ""),
            "embedding": chunk.get("embedding", []),
        })

    logger.info(f"Uploading {len(docs)} segments for video '{video_id}' to Azure AI Search...")
    results = search_client.upload_documents(documents=docs)
    succeeded = sum(1 for r in results if r.succeeded)
    logger.info(f"Indexed {succeeded}/{len(docs)} segments for video '{video_id}'.")
    return succeeded


def _search_local_cached_chunks(video_id: str, query_vector: list[float], top_k: int = 3, threshold: float = VIDEO_CONFIDENCE_THRESHOLD) -> list[dict[str, Any]]:
    """Local vector cosine similarity fallback over cached chunks."""
    cache_file = CACHE_DIR / f"{video_id}.json"
    if not cache_file.exists():
        return []

    with open(cache_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    chunks = data.get("chunks", [])
    if not chunks:
        return []

    q_vec = np.array(query_vector, dtype=np.float32)
    q_norm = np.linalg.norm(q_vec)
    if q_norm > 0:
        q_vec = q_vec / q_norm

    scored_chunks = []
    for idx, chunk in enumerate(chunks):
        c_vec = np.array(chunk.get("embedding", []), dtype=np.float32)
        c_norm = np.linalg.norm(c_vec)
        if c_norm > 0:
            c_vec = c_vec / c_norm
        cosine_sim = float(np.dot(q_vec, c_vec))
        # Map cosine [-1, 1] to Azure Search metric [0, 1]
        search_score = round((1.0 + cosine_sim) / 2.0, 4)

        scored_chunks.append({
            "id": f"{video_id}_{idx}",
            "video_id": video_id,
            "start_time": chunk.get("start_time"),
            "end_time": chunk.get("end_time"),
            "topic": chunk.get("topic"),
            "transcript": chunk.get("transcript"),
            "similarity_score": search_score,
            "is_confident": search_score >= threshold,
        })

    scored_chunks.sort(key=lambda x: x["similarity_score"], reverse=True)
    return scored_chunks[:top_k]


def search_video_segments(
    video_id: str,
    query: str,
    top_k: int = 3,
    threshold: float = VIDEO_CONFIDENCE_THRESHOLD,
) -> list[dict[str, Any]]:
    """Searches video segments using dense text vector similarity filtered by video_id."""
    query_vector = generate_transcript_embedding(query)

    try:
        # Ensure index exists in Azure AI Search
        ensure_video_segments_index()
        search_client = get_video_search_client()

        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=top_k,
            fields="embedding",
        )

        filter_expr = f"video_id eq '{video_id}'"

        search_results = search_client.search(
            search_text=None,
            vector_queries=[vector_query],
            filter=filter_expr,
            select=["id", "video_id", "start_time", "end_time", "topic", "transcript"],
            top=top_k,
        )

        matches = []
        for doc in search_results:
            score = round(float(doc.get("@search.score", 0.0)), 4)
            matches.append({
                "id": doc.get("id"),
                "video_id": doc.get("video_id"),
                "start_time": doc.get("start_time"),
                "end_time": doc.get("end_time"),
                "topic": doc.get("topic"),
                "transcript": doc.get("transcript"),
                "similarity_score": score,
                "is_confident": score >= threshold,
            })

        if matches:
            return matches

    except Exception as e:
        logger.warning(f"Azure Search query for video segments failed or index empty ({e}). Using local vector fallback.")

    # Local vector search fallback
    return _search_local_cached_chunks(video_id, query_vector, top_k=top_k, threshold=threshold)


def grounded_video_qa(
    video_id: str,
    question: str,
    top_k: int = 3,
    threshold: float = VIDEO_CONFIDENCE_THRESHOLD,
) -> dict[str, Any]:
    """Answers questions regarding video content with exact grounded start/end timestamps.

    If no confident matching segment exists, honestly reports that the information was not found.
    """
    matches = search_video_segments(video_id=video_id, query=question, top_k=top_k, threshold=threshold)

    if not matches or not matches[0]["is_confident"]:
        return {
            "video_id": video_id,
            "question": question,
            "found_match": False,
            "answer": f"No relevant segment matching your question was found in video '{video_id}'.",
            "start_time": None,
            "end_time": None,
            "similarity_score": matches[0]["similarity_score"] if matches else 0.0,
            "supporting_segment": None,
            "all_candidates": matches,
        }

    best_match = matches[0]
    start_t = best_match["start_time"]
    end_t = best_match["end_time"]
    transcript_text = best_match["transcript"]
    topic = best_match["topic"]

    video_context = (
        f"Video ID: {video_id}\n"
        f"Relevant Timestamp Interval: {start_t:.1f}s to {end_t:.1f}s\n"
        f"Segment Topic: {topic}\n"
        f"Spoken Transcript Segment: \"{transcript_text}\""
    )

    try:
        from services.llm import generate_grounded_answer
        answer = generate_grounded_answer(
            user_question=question,
            retrieved_context=video_context,
            system_instruction=(
                f"You are VisionIQ's Grounded Video Intelligence Assistant. "
                f"Answer the user's question accurately using ONLY the provided timestamped video segment ({start_t:.1f}s-{end_t:.1f}s). "
                f"Cite the exact start and end timestamps and explain what was said or shown. Do not hallucinate."
            ),
        )
    except Exception as e:
        logger.warning(f"LLM generation bypassed/failed ({e}); using timestamped transcript format.")
        answer = f"Between {start_t:.1f}s and {end_t:.1f}s ({topic}), the video covers: \"{transcript_text}\""

    return {
        "video_id": video_id,
        "question": question,
        "found_match": True,
        "answer": answer,
        "start_time": start_t,
        "end_time": end_t,
        "topic": topic,
        "similarity_score": best_match["similarity_score"],
        "supporting_segment": transcript_text,
        "all_candidates": matches,
    }


def generate_video_summary(video_id: str) -> dict[str, Any]:
    """Generates a structured summary and 3-5 key topics from a video's cached analysis."""
    cache_file = CACHE_DIR / f"{video_id}.json"
    if not cache_file.exists():
        raise FileNotFoundError(f"No analysis found for video_id: {video_id}. Please analyze the video first.")

    with open(cache_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    filename = data.get("filename", "")
    duration = data.get("duration_seconds", 0.0)
    full_transcript = data.get("full_transcript", "").strip()
    chunks = data.get("chunks", [])

    topics = []
    for chunk in chunks:
        t = chunk.get("topic", "").strip()
        if t and t not in topics:
            topics.append(t)
        if len(topics) >= 5:
            break

    if not topics and chunks:
        topics = [f"Scene at {c.get('start_time', 0.0)}s-{c.get('end_time', 0.0)}s" for c in chunks[:4]]

    if full_transcript:
        summary_text = (
            f"This video ({filename}, {duration:.1f}s) discusses the following key aspects: "
            + (full_transcript[:250] + "..." if len(full_transcript) > 250 else full_transcript)
        )
    else:
        summary_text = (
            f"This video ({filename}, {duration:.1f}s) contains {len(chunks)} visual segments "
            f"and {data.get('total_keyframes', 0)} keyframes across its timeline."
        )

    return {
        "video_id": video_id,
        "filename": filename,
        "duration_seconds": duration,
        "summary": summary_text,
        "key_topics": topics[:5],
        "total_segments": len(chunks),
    }
