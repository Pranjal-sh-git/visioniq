"""Integration tests for all VisionIQ FastAPI backend routes."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_check():
    """Verify that GET /api/health returns 200 and status ok."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_product_by_id():
    """Verify that GET /api/product/P001 returns product details."""
    response = client.get("/api/product/P001")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "P001"
    assert "Sony" in data["brand"]
    assert "specifications" in data


def test_identify_product_by_image_url():
    """Verify POST /api/product/identify with image_url."""
    response = client.post(
        "/api/product/identify",
        data={"image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=800&q=80", "top_k": 3},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["best_match"]["id"] == "P001"
    assert data["is_confident_match"] is True


def test_agent_query_product_rag():
    """Verify POST /api/agent/query routes to search_product_knowledge."""
    response = client.post(
        "/api/agent/query",
        json={"prompt": "What is its battery life?", "product_id": "P001"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["selected_tool"] == "search_product_knowledge"
    assert "30 hours" in data["tool_output"]["answer"]


def test_agent_query_clarification():
    """Verify POST /api/agent/query asks for clarification when product context is missing."""
    response = client.post(
        "/api/agent/query",
        json={"prompt": "What is its battery life?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tool_output"].get("requires_clarification") is True


def test_video_search_endpoint():
    """Verify POST /api/video/search returns grounded temporal answer."""
    response = client.post(
        "/api/video/search",
        json={
            "video_id": "vid_df16da8f30f96fb6",
            "query": "How many people can fit in the audience?",
            "top_k": 3,
            "confidence_threshold": 0.65,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["found_match"] is True
    assert data["start_time"] is not None


def test_video_summary_endpoint():
    """Verify GET /api/video/{video_id}/summary returns executive summary."""
    response = client.get("/api/video/vid_df16da8f30f96fb6/summary")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "key_topics" in data
