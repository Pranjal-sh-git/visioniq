"""Test and validation script for video search retrieval ranking bug fix."""

import json
import logging
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from services.video.processor import analyze_video
from services.video.search import search_video_segments, grounded_video_qa, VIDEO_INDEX_NAME, get_search_index_client

logging.basicConfig(level=logging.INFO)

def run_retrieval_quality_validation():
    video_path = BASE_DIR / "data" / "sample_videos" / "test_audio_video.mp4"
    if not video_path.exists():
        video_path = BASE_DIR / "data" / "uploads" / "videos" / "test_audio_video.mp4"

    print(f"Testing video at: {video_path}")
    
    # 1. Force re-analysis to compute new 384-dim embeddings and upload to Azure AI Search
    res = analyze_video(video_path, force_reprocess=True)
    video_id = res["video_id"]
    print(f"Video ID: {video_id}")
    print(f"Total Chunks: {res['chunks_count']}, Indexed to Search: {res.get('indexed_segments_count')}")

    query = "How many people can fit as an audience?"
    print(f"\nQuery: '{query}'")

    # 2. Vector Search Candidates
    candidates = search_video_segments(video_id=video_id, query=query, top_k=5)
    print("\n--- Search Candidates Ranked by Similarity ---")
    for idx, cand in enumerate(candidates):
        print(f"Rank {idx+1}: Score={cand['similarity_score']:.4f} (Confident={cand['is_confident']}) | Timestamps: [{cand['start_time']}s - {cand['end_time']}s]")
        print(f"  Snippet: {cand['transcript']}")
        print()

    # 3. Grounded QA result
    qa_result = grounded_video_qa(video_id=video_id, question=query)
    print("--- Grounded QA Output ---")
    print(f"Found Match: {qa_result['found_match']}")
    print(f"Supporting Timestamps: {qa_result['start_time']}s - {qa_result['end_time']}s")
    print(f"Similarity Score: {qa_result['similarity_score']}")
    print(f"Grounded Answer: {qa_result['answer']}")

    # Assertions
    assert len(candidates) >= 2, "Expected at least 2 chunks"
    top_chunk = candidates[0]
    second_chunk = candidates[1]

    assert "eight people as an audience" in top_chunk["transcript"], "Top chunk MUST be the eight people chunk!"
    assert top_chunk["similarity_score"] > second_chunk["similarity_score"], (
        f"Expected top chunk score ({top_chunk['similarity_score']}) > second chunk score ({second_chunk['similarity_score']})"
    )
    assert qa_result["found_match"] is True, "QA should find confident match"
    print("\n[SUCCESS] Video Retrieval Quality Bug FIXED: Target chunk is ranked #1 with high confidence!")

if __name__ == "__main__":
    run_retrieval_quality_validation()
