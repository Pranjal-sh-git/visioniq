"""Tests for Video Analysis Pipeline and POST /api/video/analyze endpoint."""

import io
import json
from pathlib import Path
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from services.video.processor import analyze_video, compute_video_id, CACHE_DIR

client = TestClient(app)

SAMPLE_VIDEOS_DIR = Path(__file__).resolve().parent.parent / "data" / "sample_videos"
SAMPLE_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
TEST_VIDEO_PATH = SAMPLE_VIDEOS_DIR / "sample_test_video.mp4"


def generate_synthetic_test_video(output_path: Path, duration_sec: int = 25, fps: int = 10):
    """Generates a synthetic MP4 video with visual countdown timestamps."""
    width, height = 320, 240
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    total_frames = duration_sec * fps
    colors = [
        (40, 40, 180),   # Red-ish
        (40, 180, 40),   # Green-ish
        (180, 40, 40),   # Blue-ish
        (180, 180, 40),  # Cyan
        (180, 40, 180),  # Magenta
    ]

    for frame_idx in range(total_frames):
        current_sec = frame_idx / fps
        color_idx = int(current_sec / 5) % len(colors)
        frame = np.full((height, width, 3), colors[color_idx], dtype=np.uint8)

        text = f"VisionIQ Test: {int(current_sec):02d}s"
        cv2.putText(
            frame,
            text,
            (20, height // 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        out.write(frame)

    out.release()


@pytest.fixture(scope="session", autouse=True)
def setup_test_video():
    """Generates the test video before running tests."""
    if not TEST_VIDEO_PATH.exists():
        generate_synthetic_test_video(TEST_VIDEO_PATH, duration_sec=25, fps=10)
    return TEST_VIDEO_PATH


def test_video_processing_direct():
    """Tests the analyze_video() function directly."""
    result = analyze_video(TEST_VIDEO_PATH, force_reprocess=True, interval_sec=10.0)

    assert "video_id" in result
    assert result["duration_seconds"] >= 24.0
    assert result["total_keyframes"] >= 3
    assert len(result["chunks"]) >= 1
    assert result["cached"] is False

    for chunk in result["chunks"]:
        assert "start_time" in chunk
        assert "end_time" in chunk
        assert "topic" in chunk
        assert "transcript" in chunk
        assert "embedding" in chunk
        assert len(chunk["embedding"]) == 384

    # Test Caching on repeat call
    cached_result = analyze_video(TEST_VIDEO_PATH, force_reprocess=False)
    assert cached_result["cached"] is True
    assert cached_result["video_id"] == result["video_id"]


def test_api_video_analyze_endpoint():
    """Tests POST /api/video/analyze with multipart upload."""
    with open(TEST_VIDEO_PATH, "rb") as f:
        video_bytes = f.read()

    response = client.post(
        "/api/video/analyze",
        files={"file": ("sample_test_video.mp4", io.BytesIO(video_bytes), "video/mp4")},
    )

    assert response.status_code == 200
    data = response.json()
    assert "video_id" in data
    assert "keyframes" in data
    assert "chunks" in data
    assert len(data["chunks"]) >= 1
    assert data["total_keyframes"] >= 3
