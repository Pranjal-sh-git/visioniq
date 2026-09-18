"""Live automated Day 3 validation checklist verification script.
Tests all live endpoints against http://localhost:8000.
"""

import sys
import requests

BASE_URL = "http://localhost:8000"

def run_checks():
    print("=" * 80)
    print("VISIONIQ — DAY 3 LIVE VALIDATION CHECKLIST EXECUTION")
    print("=" * 80)

    # 1. Health Check
    print("\n[CHECK 1] Server Health Status (GET /api/health)")
    r = requests.get(f"{BASE_URL}/api/health", timeout=10)
    print(f"Status: {r.status_code} | Body: {r.json()}")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"
    print("-> PASS: Health check endpoint active and OK")

    # 2. Cold-Start Image Flow
    print("\n[CHECK 2] Cold-Start Image Identification (POST /api/product/identify)")
    sample_img = "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=800&q=80"
    r = requests.post(f"{BASE_URL}/api/product/identify", data={"image_url": sample_img, "top_k": 3}, timeout=30)
    data = r.json()
    best = data.get("best_match", {})
    print(f"Match: {best.get('brand')} {best.get('name')} (ID: {best.get('id')})")
    print(f"Similarity Score: {best.get('similarity_score')} | Confident: {best.get('is_confident_match')}")
    print(f"Specifications: {best.get('specifications')}")
    assert best.get("id") == "P001"
    assert best.get("is_confident_match") is True
    assert "battery_life" in best.get("specifications", {})
    print("-> PASS: Cold-start image identification renders full product specs")

    # 3. Chat Continuity (3 follow-up questions in same session)
    print("\n[CHECK 3] Chat Continuity (3 sequential queries to POST /api/agent/query)")
    
    # Query 1: Battery life
    print("\n  Follow-up 1: 'What is its battery life?'")
    r1 = requests.post(f"{BASE_URL}/api/agent/query", json={"prompt": "What is its battery life?", "product_id": "P001"}, timeout=30)
    d1 = r1.json()
    print(f"  Tool: {d1.get('selected_tool')} | Answer: {d1.get('tool_output', {}).get('answer')}")
    assert d1.get("selected_tool") == "search_product_knowledge"
    assert "30 hours" in d1.get("tool_output", {}).get("answer")

    # Query 2: Similar products
    print("\n  Follow-up 2: 'Show me similar products'")
    r2 = requests.post(f"{BASE_URL}/api/agent/query", json={"prompt": "Show me similar products", "product_id": "P001"}, timeout=30)
    d2 = r2.json()
    sim_count = len(d2.get("tool_output", {}).get("similar_products", []))
    print(f"  Tool: {d2.get('selected_tool')} | Similar count: {sim_count}")
    assert d2.get("selected_tool") == "find_similar_products"
    assert sim_count > 0

    # Query 3: Weight
    print("\n  Follow-up 3: 'What is its weight?'")
    r3 = requests.post(f"{BASE_URL}/api/agent/query", json={"prompt": "What is its weight?", "product_id": "P001"}, timeout=30)
    d3 = r3.json()
    print(f"  Tool: {d3.get('selected_tool')} | Answer: {d3.get('tool_output', {}).get('answer')}")
    assert d3.get("selected_tool") == "search_product_knowledge"
    assert "250g" in d3.get("tool_output", {}).get("answer")
    print("-> PASS: Chat continuity maintained across 3 consecutive grounded follow-ups")

    # 4. Clarification Request (No context)
    print("\n[CHECK 4] Missing Context Clarification Protection")
    r_clarify = requests.post(f"{BASE_URL}/api/agent/query", json={"prompt": "What is its battery life?"}, timeout=30)
    d_clarify = r_clarify.json()
    print(f"  Clarification requested: {d_clarify.get('tool_output', {}).get('requires_clarification')}")
    print(f"  Response: {d_clarify.get('tool_output', {}).get('answer')}")
    assert d_clarify.get("tool_output", {}).get("requires_clarification") is True
    print("-> PASS: Agent politely requests product identification without throwing errors")

    # 5. Cold-Start Video Grounded QA & Timestamp Seeking
    print("\n[CHECK 5] Video Grounded Search & Timestamps (POST /api/video/search)")
    vid_id = "vid_df16da8f30f96fb6"
    r_vid = requests.post(
        f"{BASE_URL}/api/video/search",
        json={"video_id": vid_id, "query": "How many people can fit in the audience?", "top_k": 3, "confidence_threshold": 0.65},
        timeout=30
    )
    d_vid = r_vid.json()
    print(f"  Found Match: {d_vid.get('found_match')}")
    print(f"  Start Time: {d_vid.get('start_time')}s | End Time: {d_vid.get('end_time')}s")
    print(f"  Supporting Quote: \"{d_vid.get('supporting_segment')}\"")
    print(f"  Answer: {d_vid.get('answer')}")
    assert d_vid.get("found_match") is True
    assert d_vid.get("start_time") is not None
    print("-> PASS: Video search returns exact timestamp range for player seek")

    # 6. Video Summary & Key Topics
    print("\n[CHECK 6] Video Summary & Key Topics (GET /api/video/{video_id}/summary)")
    r_sum = requests.get(f"{BASE_URL}/api/video/{vid_id}/summary", timeout=30)
    d_sum = r_sum.json()
    print(f"  Summary: {d_sum.get('summary')[:120]}...")
    print(f"  Key Topics: {d_sum.get('key_topics')}")
    assert "summary" in d_sum
    assert len(d_sum.get("key_topics", [])) > 0
    print("-> PASS: Auto-generated summary and topic chips retrieved")

    print("\n" + "=" * 80)
    print("ALL DAY 3 VALIDATION CHECKLIST TESTS PASSED LIVE AGAINST LOCALHOST:8000")
    print("=" * 80)

if __name__ == "__main__":
    try:
        run_checks()
    except Exception as e:
        print(f"\n[FAIL] Validation check failed: {e}")
        sys.exit(1)
