"""Unified Day 1 and Day 2 Validation Suite for VisionIQ with real gpt-5-mini model.

Executes a single end-to-end verification pass over:
- Day 1: Product identification (known + unknown), RAG grounding on existing field, RAG honesty on missing field, missing context clarification.
- Day 2: Video search grounding, video search honesty, Agent tool routing (all 4 tools), single-tool-call fresh session verification.
"""

import io
import json
import logging
import sys
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from agent.agent import VisionIQAgent
from services.product_search.matcher import identify_product
from services.rag.rag_service import answer_product_question
from services.video.search import grounded_video_qa

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("validation")


def run_day1_validation():
    print("\n" + "=" * 80)
    print("DAY 1 VALIDATION: Product Identification, RAG Grounding & Honesty")
    print("=" * 80)

    # 1. Product Identification - Known Image
    print("\n--- Test 1.1: Product Identification (Known Image P001) ---")
    p001_img_url = "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=800&q=80"
    id_known = identify_product(image=p001_img_url, top_k=3)
    best_known = id_known[0] if id_known else {}
    print(f"Match: {best_known.get('name')} (ID: {best_known.get('id')})")
    print(f"Similarity Score: {best_known.get('similarity_score'):.4f} | Is Confident: {best_known.get('is_confident_match')}")
    assert best_known.get("id") == "P001", f"Expected P001, got {best_known.get('id')}"
    assert best_known.get("is_confident_match") is True, "Expected confident match for known image"

    # 2. Product Identification - Unknown Image (blank gray image)
    print("\n--- Test 1.2: Product Identification (Unknown Image) ---")
    blank_img = Image.new("RGB", (200, 200), color=(128, 128, 128))
    id_unknown = identify_product(image=blank_img, top_k=3, confidence_threshold=0.88)
    best_unknown = id_unknown[0] if id_unknown else {}
    print(f"Top Match Candidate: {best_unknown.get('name')} | Similarity Score: {best_unknown.get('similarity_score', 0):.4f}")
    print(f"Is Confident Match: {best_unknown.get('is_confident_match', False)}")
    # Blank noise should not pass high confidence
    assert best_unknown.get("is_confident_match", False) is False, "Unknown image must NOT be marked confident match"

    # 3. RAG Grounding on Existing Field
    print("\n--- Test 1.3: RAG Grounding on Existing Field (P001 battery life) ---")
    rag_existing = answer_product_question("P001", "What is its battery life?")
    print(f"Product: {rag_existing.get('product_name')} ({rag_existing.get('product_id')})")
    print(f"Catalog Value: {rag_existing.get('catalog_value')}")
    print(f"Actual LLM Answer: '{rag_existing.get('answer')}'")
    print(f"Grounding Field: {rag_existing.get('grounded_field')} | Hallucination Detected: {rag_existing.get('hallucination')}")
    assert rag_existing.get("is_available") is True
    assert rag_existing.get("hallucination") is False
    assert "30 hours" in rag_existing.get("answer")

    # 4. RAG Honesty on Missing Field
    print("\n--- Test 1.4: RAG Honesty on Missing Field (P001 waterproof rating) ---")
    rag_missing = answer_product_question("P001", "What is its waterproof IPX rating for swimming?")
    print(f"Product: {rag_missing.get('product_name')}")
    print(f"Actual LLM Answer: '{rag_missing.get('answer')}'")
    print(f"Is Available: {rag_missing.get('is_available')} | Hallucination Detected: {rag_missing.get('hallucination')}")
    assert rag_missing.get("is_available") is False
    assert rag_missing.get("hallucination") is False
    assert any(p in rag_missing.get("answer").lower() for p in ["not specified", "not listed", "do not list", "does not specify", "not present", "not available"])

    # 5. Clarification on Missing Context
    print("\n--- Test 1.5: Clarification on Missing Product Context ---")
    rag_clarify = answer_product_question(None, "What is its battery life?")
    print(f"Requires Clarification: {rag_clarify.get('requires_clarification')}")
    print(f"Clarification Prompt: '{rag_clarify.get('answer')}'")
    assert rag_clarify.get("requires_clarification") is True
    assert "Which product are you asking about?" in rag_clarify.get("answer")

    print("\n[SUCCESS] All Day 1 Validation checks passed perfectly!")


def run_day2_validation():
    print("\n" + "=" * 80)
    print("DAY 2 VALIDATION: Video Grounding & Honesty, Agent Tool Routing (Real gpt-5-mini)")
    print("=" * 80)

    video_id = "vid_df16da8f30f96fb6"

    # 1. Video Search Grounding
    print("\n--- Test 2.1: Video Search Grounding (Audience capacity) ---")
    video_grounded = grounded_video_qa(video_id, "How many people can fit as an audience in the area?")
    print(f"Found Match: {video_grounded.get('found_match')}")
    print(f"Interval: {video_grounded.get('start_time')}s - {video_grounded.get('end_time')}s")
    print(f"Supporting Transcript: \"{video_grounded.get('supporting_segment')}\"")
    print(f"Actual LLM Answer: '{video_grounded.get('answer')}'")
    assert video_grounded.get("found_match") is True
    assert video_grounded.get("start_time") is not None
    assert "8" in video_grounded.get("answer") or "eight" in video_grounded.get("answer").lower()

    # 2. Video Search Honesty
    print("\n--- Test 2.2: Video Search Honesty (Completely non-existent topic) ---")
    video_unmatched = grounded_video_qa(video_id, "What did the speaker say about deep sea scuba diving in Antarctica?", threshold=0.85)
    print(f"Found Match: {video_unmatched.get('found_match')}")
    print(f"Actual Answer: '{video_unmatched.get('answer')}'")
    print(f"Timestamps: {video_unmatched.get('start_time')}s - {video_unmatched.get('end_time')}s")
    assert video_unmatched.get("found_match") is False
    assert video_unmatched.get("start_time") is None
    assert "No relevant segment" in video_unmatched.get("answer")

    # 3. Agent Tool Routing (All 4 Tools with real gpt-5-mini tool-calling)
    agent = VisionIQAgent()

    print("\n--- Test 2.3: Tool Routing 1/4 -> identify_product ---")
    r1 = agent.run("What is this product?", media_url="https://images.unsplash.com/photo-1546435770-a3e426bf472b")
    print(f"Selected Tool: {r1['selected_tool']} | Reasoning: {r1['routing_reasoning']}")
    assert r1["selected_tool"] == "identify_product"

    print("\n--- Test 2.4: Tool Routing 2/4 -> search_product_knowledge ---")
    r2 = agent.run("What is its weight?", product_id="P001")
    print(f"Selected Tool: {r2['selected_tool']} | Reasoning: {r2['routing_reasoning']}")
    print(f"Answer: {r2['tool_output'].get('answer')}")
    assert r2["selected_tool"] == "search_product_knowledge"
    assert "250g" in r2["tool_output"].get("answer")

    print("\n--- Test 2.5: Tool Routing 3/4 -> search_video ---")
    r3 = agent.run("What did the speaker say about audience capacity?", video_id=video_id)
    print(f"Selected Tool: {r3['selected_tool']} | Reasoning: {r3['routing_reasoning']}")
    assert r3["selected_tool"] == "search_video"

    print("\n--- Test 2.6: Tool Routing 4/4 -> find_similar_products ---")
    r4 = agent.run("Show me products similar to this one", product_id="P001")
    print(f"Selected Tool: {r4['selected_tool']} | Reasoning: {r4['routing_reasoning']}")
    assert r4["selected_tool"] == "find_similar_products"

    # 4. Single-Tool-Call Verification on Fresh Session
    print("\n--- Test 2.7: Single-Tool-Call Verification (Fresh session: 'What is its battery life?') ---")
    r_fresh = agent.run("What is its battery life?", product_id=None)
    print(f"Selected Tool: {r_fresh['selected_tool']}")
    print(f"Tool Output: {r_fresh['tool_output']}")
    assert r_fresh["selected_tool"] == "search_product_knowledge"
    assert r_fresh["tool_output"].get("requires_clarification") is True
    assert "Which product are you asking about?" in r_fresh["tool_output"].get("answer")

    print("\n[SUCCESS] All Day 2 Validation checks passed perfectly!")


if __name__ == "__main__":
    run_day1_validation()
    run_day2_validation()
    print("\n" + "=" * 80)
    print("ALL DAY 1 AND DAY 2 VALIDATION TESTS PASSED WITH REAL GPT-5-MINI!")
    print("=" * 80)
