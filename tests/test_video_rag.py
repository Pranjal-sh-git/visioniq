"""Tests for Video RAG, Semantic Search, and Video Summarization."""

import io
from pathlib import Path
import sys
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
for directory in (str(ROOT_DIR), str(ROOT_DIR / "backend")):
    if directory not in sys.path:
        sys.path.insert(0, directory)

from fastapi.testclient import TestClient
from backend.main import app
from services.video.processor import analyze_video
from services.video.search import grounded_video_qa, generate_video_summary

client = TestClient(app)

SAMPLE_VIDEOS_DIR = Path(__file__).resolve().parent.parent / "data" / "sample_videos"
SAMPLE_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
TEST_VIDEO_PATH = SAMPLE_VIDEOS_DIR / "sample_test_video.mp4"


@pytest.fixture(scope="session", autouse=True)
def processed_video():
    """Ensures test video is analyzed and indexed in Azure AI Search."""
    result = analyze_video(TEST_VIDEO_PATH, force_reprocess=True)
    return result


def test_video_search_matching_query(processed_video):
    """Tests searching for a relevant visual or audio segment."""
    video_id = processed_video["video_id"]

    # Search via API
    response = client.post(
        "/api/video/search",
        json={"video_id": video_id, "query": "Visual scene at timestamp 10s", "top_k": 3},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == video_id
    assert data["found_match"] is True
    assert data["start_time"] is not None
    assert data["end_time"] is not None
    assert "answer" in data
    assert len(data["all_candidates"]) >= 1


def test_video_search_unmatched_query_honesty(processed_video):
    """Tests that completely unrelated queries refuse to invent timestamps."""
    video_id = processed_video["video_id"]

    # Search for something completely non-existent
    response = client.post(
        "/api/video/search",
        json={
            "video_id": video_id,
            "query": "Quantum computing cryptographic algorithms in zero gravity astrophysics",
            "confidence_threshold": 0.90,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["found_match"] is False
    assert data["start_time"] is None
    assert data["end_time"] is None
    assert "not provide enough information" in data["answer"].lower() or "no relevant segment" in data["answer"].lower()


def test_video_summary_endpoint(processed_video):
    """Tests GET /api/video/{video_id}/summary."""
    video_id = processed_video["video_id"]

    response = client.get(f"/api/video/{video_id}/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == video_id
    assert "summary" in data
    assert "key_topics" in data
    assert isinstance(data["key_topics"], list)
    assert len(data["key_topics"]) >= 1
    assert len(data["key_topics"]) <= 5
