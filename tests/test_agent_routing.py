"""Tests for VisionIQ Microsoft Foundry Agent orchestration and tool routing."""

import logging
from pathlib import Path
import sys
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


def test_agent_routing_identify_product(caplog):
    """Verifies 'What is this product?' routes to identify_product."""
    agent = VisionIQAgent()
    with caplog.at_level(logging.INFO):
        result = agent.run("What is this product?", media_url="https://images.unsplash.com/photo-1546435770-a3e426bf472b")
    
    assert result["selected_tool"] == "identify_product"
    assert "identify_product" in result["routing_reasoning"]
    assert "[ROUTING] Selected tool: 'identify_product'" in caplog.text


def test_agent_routing_search_product_knowledge(caplog):
    """Verifies 'What is its battery life?' routes to search_product_knowledge."""
    agent = VisionIQAgent()
    with caplog.at_level(logging.INFO):
        result = agent.run("What is its battery life?", product_id="P001")
    
    assert result["selected_tool"] == "search_product_knowledge"
    assert "search_product_knowledge" in result["routing_reasoning"]
    assert "[ROUTING] Selected tool: 'search_product_knowledge'" in caplog.text


def test_agent_routing_search_video(caplog):
    """Verifies 'What did the reviewer say about sound quality?' routes to search_video."""
    agent = VisionIQAgent()
    with caplog.at_level(logging.INFO):
        result = agent.run("What did the reviewer say about sound quality?", video_id="vid_df16da8f30f96fb6")
    
    assert result["selected_tool"] == "search_video"
    assert "search_video" in result["routing_reasoning"]
    assert "[ROUTING] Selected tool: 'search_video'" in caplog.text


def test_agent_routing_find_similar_products(caplog):
    """Verifies 'Show me similar products' routes to find_similar_products."""
    agent = VisionIQAgent()
    with caplog.at_level(logging.INFO):
        result = agent.run("Show me similar products", product_id="P001")
    
    assert result["selected_tool"] == "find_similar_products"
    assert "find_similar_products" in result["routing_reasoning"]
    assert "[ROUTING] Selected tool: 'find_similar_products'" in caplog.text


if __name__ == "__main__":
    agent = VisionIQAgent()
    prompts = [
        ("What is this product?", {"media_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b"}),
        ("What is its battery life?", {"product_id": "P001"}),
        ("What did the speaker say about audience capacity?", {"video_id": "vid_df16da8f30f96fb6"}),
        ("Show me similar products", {"product_id": "P001"}),
    ]
    print("\n--- Running Live Agent Routing Tests ---")
    for prompt, kwargs in prompts:
        res = agent.run(prompt, **kwargs)
        print(f"\nUser Query: '{prompt}'")
        print(f"  -> Tool Selected: {res['selected_tool']}")
        print(f"  -> Reasoning: {res['routing_reasoning']}")
        print(f"  -> Output Summary: {type(res['tool_output'])}")
