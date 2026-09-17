"""Tests for VisionIQ Microsoft Foundry Agent orchestration and tool routing."""

import json
import logging
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from agent.agent import VisionIQAgent

def test_agent_tool_schemas_registered():
    """Verifies that all 4 Microsoft Foundry Agent tool definitions are properly registered."""
    agent = VisionIQAgent()
    tools = agent.get_tool_definitions()
    assert len(tools) == 4
    tool_names = [t["function"]["name"] for t in tools]
    assert "identify_product" in tool_names
    assert "search_product_knowledge" in tool_names
    assert "search_video" in tool_names
    assert "find_similar_products" in tool_names


def make_mock_completion(tool_name: str, arguments: dict):
    """Helper to mock Azure OpenAI ChatCompletion response."""
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = tool_name
    mock_tool_call.function.arguments = json.dumps(arguments)

    mock_choice = MagicMock()
    mock_choice.message.tool_calls = [mock_tool_call]
    mock_choice.message.content = None

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


def test_agent_routing_identify_product(caplog):
    """Verifies 'What is this product?' routes to identify_product via model function calling."""
    agent = VisionIQAgent()
    mock_resp = make_mock_completion("identify_product", {"image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b", "top_k": 3})

    with patch("agent.agent.get_azure_openai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_resp
        mock_get_client.return_value = mock_client

        with caplog.at_level(logging.INFO):
            result = agent.run("What is this product?", media_url="https://images.unsplash.com/photo-1546435770-a3e426bf472b")

    assert result["selected_tool"] == "identify_product"
    assert "identify_product" in result["routing_reasoning"]
    assert "[ROUTING] Selected tool: 'identify_product'" in caplog.text


def test_agent_routing_search_product_knowledge(caplog):
    """Verifies 'What is its battery life?' routes to search_product_knowledge via model function calling."""
    agent = VisionIQAgent()
    mock_resp = make_mock_completion("search_product_knowledge", {"query": "What is its battery life?", "product_id": "P001"})

    with patch("agent.agent.get_azure_openai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_resp
        mock_get_client.return_value = mock_client

        with caplog.at_level(logging.INFO):
            result = agent.run("What is its battery life?", product_id="P001")

    assert result["selected_tool"] == "search_product_knowledge"
    assert "search_product_knowledge" in result["routing_reasoning"]
    assert "[ROUTING] Selected tool: 'search_product_knowledge'" in caplog.text


def test_agent_routing_search_video(caplog):
    """Verifies 'What did the reviewer say about sound quality?' routes to search_video."""
    agent = VisionIQAgent()
    mock_resp = make_mock_completion("search_video", {"video_id": "vid_df16da8f30f96fb6", "query": "What did the reviewer say about sound quality?", "top_k": 3})

    with patch("agent.agent.get_azure_openai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_resp
        mock_get_client.return_value = mock_client

        with caplog.at_level(logging.INFO):
            result = agent.run("What did the reviewer say about sound quality?", video_id="vid_df16da8f30f96fb6")

    assert result["selected_tool"] == "search_video"
    assert "search_video" in result["routing_reasoning"]
    assert "[ROUTING] Selected tool: 'search_video'" in caplog.text


def test_agent_routing_find_similar_products(caplog):
    """Verifies 'Show me similar products' routes to find_similar_products."""
    agent = VisionIQAgent()
    mock_resp = make_mock_completion("find_similar_products", {"product_id": "P001", "top_k": 4})

    with patch("agent.agent.get_azure_openai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_resp
        mock_get_client.return_value = mock_client

        with caplog.at_level(logging.INFO):
            result = agent.run("Show me similar products", product_id="P001")

    assert result["selected_tool"] == "find_similar_products"
    assert "find_similar_products" in result["routing_reasoning"]
    assert "[ROUTING] Selected tool: 'find_similar_products'" in caplog.text
