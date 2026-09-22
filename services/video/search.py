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

VIDEO_CONFIDENCE_THRESHOLD = 0.50


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


def get_video_speech_segments(video_id: str) -> list[dict[str, Any]]:
    """Loads all fine-grained speech segments or chunks for a video."""
    cache_file = CACHE_DIR / f"{video_id}.json"
    if not cache_file.exists():
        return []

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 1. Direct fine-grained segments if present
        if "segments" in data and data["segments"]:
            return data["segments"]

        # 2. Fallback to chunks
        if "chunks" in data and data["chunks"]:
            chunks = data["chunks"]
            segments = []
            for c in chunks:
                segments.append({
                    "start_time": float(c.get("start_time", 0.0)),
                    "end_time": float(c.get("end_time", 0.0)),
                    "text": c.get("transcript", ""),
                })
            return segments
    except Exception as e:
        logger.warning(f"Failed to load speech segments for video {video_id}: {e}")

    return []


SETUP_QUESTION_INDICATORS = [
    "let's consider", "consider the", "let's look at", "now let's", "now we have",
    "for example", "suppose we", "suppose", "reaction between", "when we mix",
    "what do you think", "what happens when", "what will happen", "why does",
    "how does", "what is", "can someone", "let me ask", "to start with",
    "first,", "to begin with", "in this experiment", "in this problem",
    "the question is", "question is", "let us examine", "take the case of",
    "let's discuss", "we are going to", "if you take", "if we take"
]

TOPIC_SHIFT_INDICATORS = [
    "next topic", "moving on", "now turning to", "another question",
    "on the other hand", "next example", "that is all for", "let's move to",
    "now let's look at another", "in contrast", "next question", "moving to"
]


def detect_context_window(
    segments: list[dict[str, Any]],
    matched_timestamp: float,
    query: str = "",
    max_lookback_sec: float = 35.0,
    max_lookforward_sec: float = 45.0,
) -> tuple[float, float, list[dict[str, Any]]]:
    """Determines context_start, context_end, and evidence segments around matched_timestamp.

    Identifies the natural beginning of the relevant discussion (e.g. question or topic setup).
    If no natural linguistic boundary exists, uses a reasonable short buffer (~5s) before matched_timestamp.

    Returns:
        tuple[float, float, list[dict]]: (context_start, context_end, evidence_segments)
    """
    if not segments:
        context_start = max(0.0, matched_timestamp - 5.0)
        context_end = matched_timestamp + 15.0
        return context_start, context_end, []

    # Find the segment closest to matched_timestamp
    matched_idx = 0
    min_dist = float("inf")
    for idx, seg in enumerate(segments):
        st = float(seg.get("start_time", 0.0))
        dist = abs(st - matched_timestamp)
        if dist < min_dist:
            min_dist = dist
            matched_idx = idx

    # 1. Scan Backward for context_start (Look for question / topic setup / reaction introduction)
    context_start = float(segments[matched_idx].get("start_time", matched_timestamp))
    natural_start_found = False

    # Check preceding segments within max_lookback_sec
    lookback_limit_t = max(0.0, matched_timestamp - max_lookback_sec)
    for i in range(matched_idx - 1, -1, -1):
        seg = segments[i]
        seg_start = float(seg.get("start_time", 0.0))
        seg_text = seg.get("text", "").strip().lower()

        if seg_start < lookback_limit_t:
            break

        # Stop looking backward if we hit an earlier topic shift
        if any(ind in seg_text for ind in TOPIC_SHIFT_INDICATORS):
            break

        # Check for question marks, setup phrases, or query terms
        is_setup = any(ind in seg_text for ind in SETUP_QUESTION_INDICATORS) or seg_text.endswith("?")
        query_words = [w for w in query.lower().split() if len(w) > 3]
        has_query_words = any(w in seg_text for w in query_words)

        if is_setup or has_query_words:
            context_start = seg_start
            natural_start_found = True
            # Continue checking if the segment immediately before this is also an introductory setup
            continue
        elif natural_start_found:
            # Reached before the beginning of the setup cluster
            break

    # If no explicit linguistic boundary was found, apply a reasonable short buffer (~5 seconds)
    if not natural_start_found:
        if matched_idx > 0 and (matched_timestamp - float(segments[matched_idx - 1].get("start_time", 0.0))) <= 8.0:
            context_start = float(segments[matched_idx - 1].get("start_time", 0.0))
        else:
            context_start = max(0.0, matched_timestamp - 5.0)


    # 2. Scan Forward for context_end (Look for completion of explanation before topic shift)
    context_end = float(segments[matched_idx].get("end_time", matched_timestamp + 10.0))
    lookforward_limit_t = matched_timestamp + max_lookforward_sec

    for j in range(matched_idx + 1, len(segments)):
        seg = segments[j]
        seg_start = float(seg.get("start_time", 0.0))
        seg_end = float(seg.get("end_time", seg_start + 5.0))
        seg_text = seg.get("text", "").strip().lower()

        if seg_start > lookforward_limit_t:
            break

        # If a new topic or new question begins, stop immediately before this segment
        if any(ind in seg_text for ind in TOPIC_SHIFT_INDICATORS):
            break

        context_end = seg_end

    # Enforce minimum sensible window and bounds (context_start can never be less than 0:00)
    context_start = max(0.0, round(context_start, 2))
    context_end = max(context_start + 5.0, round(context_end, 2))

    # 3. Collect Evidence items bounded strictly by context_start and context_end
    evidence = [
        {"timestamp": round(float(s.get("start_time", 0.0)), 2), "text": s.get("text", "").strip()}
        for s in segments
        if float(s.get("end_time", 0.0)) >= context_start - 0.5 and float(s.get("start_time", 0.0)) <= context_end + 0.5
        and s.get("text", "").strip()
    ]

    return context_start, context_end, evidence


def search_video_segments(
    video_id: str,
    query: str,
    top_k: int = 4,
    threshold: float = VIDEO_CONFIDENCE_THRESHOLD,
) -> list[dict[str, Any]]:
    """Searches video segments using dense text vector similarity and contextual re-ranking."""
    query_vector = generate_transcript_embedding(query)
    matches: list[dict[str, Any]] = []

    try:
        # Ensure index exists in Azure AI Search
        ensure_video_segments_index()
        search_client = get_video_search_client()

        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=top_k * 2,
            fields="embedding",
        )

        filter_expr = f"video_id eq '{video_id}'"

        search_results = search_client.search(
            search_text=None,
            vector_queries=[vector_query],
            filter=filter_expr,
            select=["id", "video_id", "start_time", "end_time", "topic", "transcript"],
            top=top_k * 2,
        )

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

    except Exception as e:
        logger.warning(f"Azure Search query for video segments failed or index empty ({e}). Using local vector fallback.")

    if not matches:
        matches = _search_local_cached_chunks(video_id, query_vector, top_k=top_k * 2, threshold=threshold)

    # Disambiguate multiple mentions by scoring against surrounding contextual relevance
    query_tokens = set(w.lower() for w in query.split() if len(w) > 3)
    for m in matches:
        t_text = m.get("transcript", "").lower()
        # Count token matches in the segment transcript
        token_match_count = sum(1 for t in query_tokens if t in t_text)
        lexical_boost = min(0.15, token_match_count * 0.05)
        m["composite_score"] = round(m["similarity_score"] + lexical_boost, 4)
        m["is_confident"] = m["composite_score"] >= threshold

    matches.sort(key=lambda x: x.get("composite_score", x["similarity_score"]), reverse=True)
    return matches[:top_k]


def grounded_video_qa(
    video_id: str,
    question: str,
    top_k: int = 4,
    threshold: float = VIDEO_CONFIDENCE_THRESHOLD,
) -> dict[str, Any]:
    """Answers questions regarding video content with context-aware start/end timestamps and precise evidence grounding.

    Identifies:
      - context_start: where video playback should begin (including topic/question setup)
      - matched_timestamp: exact point where the core answer/keyword was matched
      - context_end: where the relevant explanation ends
      - evidence: list of structured timestamped quotes supporting the answer
    """
    matches = search_video_segments(video_id=video_id, query=question, top_k=top_k, threshold=threshold)

    # Detect if user is asking a video-level global summary/conclusion question
    q_clean = question.lower().strip()
    global_query_keywords = [
        "summarize", "summary", "highlight", "takeaway", "main conclusion", "conclusion",
        "verdict", "overview", "what is this video about", "what is discussed",
        "key point", "purpose", "speaker's goal", "what happens in the video", "key topics"
    ]
    is_global_query = any(k in q_clean for k in global_query_keywords)

    if is_global_query:
        cache_file = CACHE_DIR / f"{video_id}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    vdata = json.load(f)
                full_trans = vdata.get("full_transcript", "").strip()
                ai_sum = vdata.get("ai_summary", {})
                if full_trans or ai_sum:
                    summary_evidence = []
                    for s in vdata.get("segments", [])[:6]:
                        if s.get("text"):
                            summary_evidence.append({"timestamp": round(float(s.get("start_time", 0.0)), 2), "text": s.get("text", "")})
                    if not summary_evidence and vdata.get("chunks"):
                        for c in vdata.get("chunks", [])[:5]:
                            summary_evidence.append({"timestamp": round(float(c.get("start_time", 0.0)), 2), "text": c.get("transcript", "")})

                    video_context = (
                        f"Video ID: {video_id} (Filename: {vdata.get('filename', '')})\n"
                        f"Executive Summary: {ai_sum.get('summary', '')}\n"
                        f"Key Topics: {', '.join(ai_sum.get('key_topics', []))}\n"
                        f"Key Takeaways:\n" + "\n".join(f"- {t}" for t in ai_sum.get("key_takeaways", [])) + "\n\n"
                        f"Spoken Transcript Samples:\n"
                        + "\n".join(f"[{e['timestamp']}s] \"{e['text']}\"" for e in summary_evidence)
                        + (f"\n\nFull Transcript:\n{full_trans[:3500]}" if full_trans else "")
                    )

                    system_instruction = (
                        "You are VisionIQ's Grounded Video Intelligence Assistant.\n"
                        "Answer the user's question directly, accurately, and concisely (2-4 sentences max) based STRICTLY on the provided video transcript and summary.\n"
                        "Do NOT extrapolate outside information."
                    )
                    try:
                        from services.llm import generate_grounded_answer
                        global_ans = generate_grounded_answer(user_question=question, retrieved_context=video_context, system_instruction=system_instruction)
                    except Exception as e:
                        logger.warning(f"LLM global summary answer fallback: {e}")
                        global_ans = ai_sum.get("summary") or (f"This video discusses: {full_trans[:250]}" if full_trans else "Video analyzed.")

                    dur = float(vdata.get("duration_seconds", 0.0))
                    return {
                        "video_id": video_id,
                        "question": question,
                        "found_match": True,
                        "answer": global_ans,
                        "context_start": 0.0,
                        "matched_timestamp": 0.0,
                        "context_end": round(dur, 2) if dur > 0 else 30.0,
                        "start_time": 0.0,
                        "end_time": round(dur, 2) if dur > 0 else 30.0,
                        "topic": ai_sum.get("key_topics", ["Overview"])[0] if ai_sum.get("key_topics") else "Video Overview",
                        "similarity_score": 0.95,
                        "supporting_segment": ai_sum.get("summary") or (full_trans[:250] if full_trans else ""),
                        "evidence": summary_evidence[:4],
                        "all_candidates": matches,
                    }
            except Exception as e:
                logger.warning(f"Global query context resolution failed: {e}")

    if not matches or not matches[0]["is_confident"]:
        return {
            "video_id": video_id,
            "question": question,
            "found_match": False,
            "answer": "The lecture does not provide enough information to answer that specifically.",
            "context_start": None,
            "matched_timestamp": None,
            "context_end": None,
            "start_time": None,
            "end_time": None,
            "evidence": [],
            "similarity_score": matches[0]["similarity_score"] if matches else 0.0,
            "supporting_segment": None,
            "all_candidates": matches,
        }

    best_match = matches[0]
    matched_t = float(best_match["start_time"])
    transcript_text = best_match["transcript"]
    topic = best_match["topic"]

    # Load all speech segments to perform intelligent context expansion
    all_segments = get_video_speech_segments(video_id)
    if not all_segments:
        all_segments = [
            {"start_time": float(m.get("start_time", 0.0)), "end_time": float(m.get("end_time", 0.0)), "text": m.get("transcript", "")}
            for m in matches
        ]

    context_start, context_end, evidence = detect_context_window(
        segments=all_segments,
        matched_timestamp=matched_t,
        query=question,
    )

    # Format evidence into structured text for LLM grounding
    evidence_lines = "\n".join(
        f"[{int(e['timestamp'] // 60):02d}:{int(e['timestamp'] % 60):02d} ({e['timestamp']:.1f}s)] \"{e['text']}\""
        for e in evidence
    ) if evidence else f"[{matched_t:.1f}s] \"{transcript_text}\""

    video_context = (
        f"Video ID: {video_id}\n"
        f"Context Interval: {context_start:.1f}s to {context_end:.1f}s (Core match at {matched_t:.1f}s)\n"
        f"Topic: {topic}\n\n"
        f"Transcript Evidence from the Lecture:\n{evidence_lines}"
    )

    system_instruction = (
        "You are VisionIQ's Grounded Video Intelligence Assistant.\n"
        "Your goal is to answer the user's question accurately, concisely, and specifically based PRIMARILY AND DIRECTLY on the provided video transcript evidence.\n\n"
        "Rules:\n"
        "1. Be concise, direct, and factual (2-3 sentences max).\n"
        "2. Ground your answer in what the instructor/speaker/video presented. Note that automated speech recognition may have minor phonetic artifacts (e.g. 'Beauty' for Butane, 'Free on' for Freon, 'Cabo hydrates' for Carbohydrates, 'LBG' for LPG); interpret these reasonably based on the context of the question.\n"
        "3. If the discussion involves a setup or question-answer sequence (e.g., teacher asking a question then stating/explaining the answer), state the answer clearly.\n"
        "4. Do NOT include extraneous external textbook trivia or unsupported speculation.\n"
        "5. If the transcript does not contain or mention the requested topic, state: \"The lecture does not provide enough information to answer that specifically.\"\n"
        "6. Never invent information or timestamps."
    )

    try:
        from services.llm import generate_grounded_answer
        answer = generate_grounded_answer(
            user_question=question,
            retrieved_context=video_context,
            system_instruction=system_instruction,
        )
    except Exception as e:
        logger.warning(f"LLM generation bypassed/failed ({e}); using timestamped transcript format.")
        answer = f"In the lecture ({context_start:.1f}s - {context_end:.1f}s), the instructor discusses: \"{transcript_text}\""

    return {
        "video_id": video_id,
        "question": question,
        "found_match": True,
        "answer": answer,
        "context_start": round(context_start, 2),
        "matched_timestamp": round(matched_t, 2),
        "context_end": round(context_end, 2),
        "start_time": round(context_start, 2),  # Backward compatibility
        "end_time": round(context_end, 2),      # Backward compatibility
        "topic": topic,
        "similarity_score": best_match["similarity_score"],
        "supporting_segment": transcript_text,
        "evidence": evidence,
        "all_candidates": matches,
    }



def generate_video_summary(video_id: str, force_regenerate: bool = False) -> dict[str, Any]:
    """Generates a rich, structured AI summary, key topics, and key takeaways from a video's transcript.

    Uses Azure OpenAI (gpt-5-mini) to analyze the full transcribed speech of the video,
    extracting an executive summary, key discussion topics, and bulleted takeaways.
    Caches the generated summary back into the video cache for high performance.
    """
    cache_file = CACHE_DIR / f"{video_id}.json"
    if not cache_file.exists():
        raise FileNotFoundError(f"No analysis found for video_id: {video_id}. Please analyze the video first.")

    with open(cache_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    filename = data.get("filename", "")
    duration = data.get("duration_seconds", 0.0)
    full_transcript = data.get("full_transcript", "").strip()
    chunks = data.get("chunks", [])

    # If already cached and force_regenerate is False, return cached AI summary
    if not force_regenerate and "ai_summary" in data and data["ai_summary"]:
        cached_summary = data["ai_summary"]
        return {
            "video_id": video_id,
            "filename": filename,
            "duration_seconds": duration,
            "summary": cached_summary.get("summary", ""),
            "key_topics": cached_summary.get("key_topics", []),
            "key_takeaways": cached_summary.get("key_takeaways", []),
            "total_segments": len(chunks),
            "full_transcript": full_transcript,
        }

    # Extract default fallback topics from chunk headers
    fallback_topics = []
    for chunk in chunks:
        t = chunk.get("topic", "").strip()
        if t and t not in fallback_topics:
            fallback_topics.append(t)
        if len(fallback_topics) >= 5:
            break

    if not fallback_topics and chunks:
        fallback_topics = [f"Scene at {c.get('start_time', 0.0):.1f}s-{c.get('end_time', 0.0):.1f}s" for c in chunks[:4]]

    summary_text = ""
    key_topics = fallback_topics
    key_takeaways = []

    if full_transcript:
        try:
            from services.llm import get_azure_openai_client
            from backend.config import settings

            client = get_azure_openai_client()
            deployment = settings.AZURE_OPENAI_DEPLOYMENT_NAME

            sys_prompt = (
                "You are VisionIQ's Expert Multimodal Video & Lecture Intelligence Summarizer.\n"
                "Your task is to analyze the complete transcribed speech from an audio/video recording and produce a comprehensive, well-structured, and strictly transcript-grounded summary.\n\n"
                "Guidelines:\n"
                "1. Executive Summary: 2 to 4 clear, articulate sentences summarizing the core topic, key arguments or explanations, and conclusions reached by the speaker.\n"
                "2. Key Topics: 3 to 6 concise topic phrases covering the major concepts discussed.\n"
                "3. Key Takeaways: 3 to 5 concise bullet points highlighting the most important findings, explanations, or statements.\n"
                "4. Maintain strict factual grounding in what was actually spoken in the transcript without hallucinating outside facts.\n\n"
                "Respond ONLY in valid JSON format matching this schema:\n"
                "{\n"
                '  "summary": "Concise 2-4 sentence executive summary...",\n'
                '  "key_topics": ["Topic 1", "Topic 2", "Topic 3"],\n'
                '  "key_takeaways": ["Takeaway 1", "Takeaway 2", "Takeaway 3"]\n'
                "}"
            )

            user_prompt = (
                f"Video Title / Filename: {filename}\n"
                f"Duration: {duration:.1f} seconds\n\n"
                f"Full Transcribed Speech:\n\"\"\"\n{full_transcript}\n\"\"\"\n\n"
                "Please generate the structured summary JSON."
            )

            logger.info(f"Generating LLM transcript summary for video '{video_id}' ({filename})...")
            response = client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_completion_tokens=1500,
            )

            raw_content = (response.choices[0].message.content or "").strip()
            # Clean markdown fences if any
            if raw_content.startswith("```json"):
                raw_content = raw_content[7:]
            if raw_content.startswith("```"):
                raw_content = raw_content[3:]
            if raw_content.endswith("```"):
                raw_content = raw_content[:-3]
            raw_content = raw_content.strip()

            parsed_data = json.loads(raw_content)
            summary_text = parsed_data.get("summary", "").strip()
            if parsed_data.get("key_topics"):
                key_topics = [str(t).strip() for t in parsed_data["key_topics"] if str(t).strip()]
            if parsed_data.get("key_takeaways"):
                key_takeaways = [str(t).strip() for t in parsed_data["key_takeaways"] if str(t).strip()]

        except Exception as e:
            logger.warning(f"LLM transcript summarization failed ({e}); falling back to heuristic summary.")
            summary_text = (
                f"In this video ({filename}, {duration:.1f}s), the speaker discusses: "
                + (full_transcript[:300] + "..." if len(full_transcript) > 300 else full_transcript)
            )
            key_takeaways = [f"Transcript dialogue: \"{s.get('text', '')[:120]}\"" for s in data.get("segments", [])[:3] if s.get("text")]
    else:
        summary_text = (
            f"This video ({filename}, {duration:.1f}s) contains {len(chunks)} visual segments "
            f"and {data.get('total_keyframes', 0)} keyframes across its timeline (no spoken audio detected)."
        )

    # Cache AI summary back into data file
    ai_summary_obj = {
        "summary": summary_text,
        "key_topics": key_topics,
        "key_takeaways": key_takeaways,
    }
    try:
        data["ai_summary"] = ai_summary_obj
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Could not persist ai_summary to cache file: {e}")

    return {
        "video_id": video_id,
        "filename": filename,
        "duration_seconds": duration,
        "summary": summary_text,
        "key_topics": key_topics[:6],
        "key_takeaways": key_takeaways[:6],
        "total_segments": len(chunks),
        "full_transcript": full_transcript,
    }

