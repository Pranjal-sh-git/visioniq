"""Live validation script for Microsoft Foundry Azure OpenAI Agent and RAG."""

import json
import logging
import os
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from agent.agent import VisionIQAgent
from services.rag.rag_service import answer_product_question
from services.video.search import grounded_video_qa

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("live_validation")


def run_live_agent_and_rag_suite():
    print("\n" + "=" * 75)
    print("VISIONIQ MICROSOFT FOUNDRY (GPT-5-MINI) LIVE VALIDATION SUITE")
    print("=" * 75)

    agent = VisionIQAgent()
    print(f"Agent Configured Deployment: {agent.deployment_name}")
    print(f"Registered Tools: {[t['function']['name'] for t in agent.get_tool_definitions()]}")
    print("-" * 75)

    test_queries = [
        ("1. Product Identification", "What is this product?", {"media_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b"}),
        ("2. Product Catalog RAG", "What is its battery life?", {"product_id": "P001"}),
        ("3. Temporal Video Search", "What did the speaker say about audience capacity in the video?", {"video_id": "vid_df16da8f30f96fb6"}),
        ("4. Similar Products Recommendation", "Show me similar products", {"product_id": "P001"}),
    ]

    for label, query, kwargs in test_queries:
        print(f"\n--- TEST: {label} ---")
        print(f"Prompt: \"{query}\"")
        try:
            res = agent.run(query, **kwargs)
            print(f"  [RESULT] Selected Tool: {res['selected_tool']}")
            print(f"  [RESULT] Parameters: {res['tool_parameters']}")
            print(f"  [RESULT] Reasoning: {res['routing_reasoning']}")
        except Exception as e:
            print(f"  [EXECUTION NOTE] {e}")

    print("\n" + "=" * 75)
    print("RAG GROUNDING & ANSWER GENERATION VALIDATION")
    print("=" * 75)
    print("Querying Product Knowledge RAG for P001 battery life...")
    rag_result = answer_product_question("P001", "What is its battery life?")
    print(f"RAG Grounded Answer: {rag_result.get('answer')}")

    print("\nQuerying Video Temporal Search for vid_df16da8f30f96fb6...")
    video_result = grounded_video_qa("vid_df16da8f30f96fb6", "How many people can fit as an audience?")
    print(f"Video Grounded Answer: {video_result.get('answer')}")
    print(f"Timestamps: {video_result.get('start_time')}s - {video_result.get('end_time')}s")
    print("=" * 75)


if __name__ == "__main__":
    run_live_agent_and_rag_suite()
