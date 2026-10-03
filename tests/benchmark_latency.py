"""Benchmark latency for Q&A path and Identify path.

Executes 5 requests per endpoint with PROFILE_TIMING=1 and records
stage timing: request parse, image fetch, CLIP embedding, AI Search query,
LLM call, response serialization.
"""

import json
import logging
import os
from pathlib import Path
import statistics
import sys
import time

# Set environment variable before importing app
os.environ["PROFILE_TIMING"] = "1"

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
for d in (str(PROJECT_ROOT), str(PROJECT_ROOT / "backend")):
    if d not in sys.path:
        sys.path.insert(0, d)

from fastapi.testclient import TestClient
from backend.main import app
from backend.timing import set_timing_collector

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("benchmark")


def main():
    print("Initializing TestClient...")
    client = TestClient(app)

    # Dictionary to collect timing measurements per endpoint and stage
    # Keys will be e.g. 'qa:request_parse', 'identify:clip_embedding', etc.
    collector = {}
    set_timing_collector(collector)

    qa_prompts = [
        {"prompt": "What is the battery life of the Sony WH-1000XM5 headphones?", "product_id": "P001"},
        {"prompt": "What are the key ergonomic adjustments for the Herman Miller Aeron Chair?", "product_id": "P006"},
        {"prompt": "What is the weight and noise cancellation feature of the Apple AirPods Max?", "product_id": "P003"},
        {"prompt": "Does the Bose QuietComfort Ultra support wireless Bluetooth connectivity?", "product_id": "P002"},
        {"prompt": "What upper and midsole cushioning material is used in Nike Air Zoom Pegasus 40?", "product_id": "P011"},
    ]

    print("\n" + "=" * 60)
    print("RUNNING 5 REQUESTS FOR Q&A PATH (/api/agent/query)")
    print("=" * 60)

    for i, payload in enumerate(qa_prompts, 1):
        print(f"\n--- Q&A Request {i}/5: {payload['prompt'][:45]}... ---")
        t0 = time.perf_counter()
        resp = client.post("/api/agent/query", json=payload)
        t_total = time.perf_counter() - t0
        print(f"Status: {resp.status_code} | Total HTTP Roundtrip: {t_total:.4f}s")
        if resp.status_code != 200:
            print("Response error:", resp.text)

    # Identify image paths
    image_dir = PROJECT_ROOT / "data" / "uploads" / "images"
    sample_images = [
        image_dir / "download.png",
        image_dir / "r1-mens.png",
        image_dir / "61wSmw6oC7L._AC_.jpg",
        image_dir / "download.png",
        image_dir / "r1-mens.png",
    ]

    print("\n" + "=" * 60)
    print("RUNNING 5 REQUESTS FOR IDENTIFY PATH (/api/product/identify)")
    print("=" * 60)

    for i, img_path in enumerate(sample_images, 1):
        print(f"\n--- Identify Request {i}/5: {img_path.name} ---")
        if not img_path.exists():
            print(f"File {img_path} not found, skipping...")
            continue
        t0 = time.perf_counter()
        with open(img_path, "rb") as f:
            files = {"file": (img_path.name, f, "image/png" if img_path.suffix == ".png" else "image/jpeg")}
            data = {"top_k": "3", "confidence_threshold": "0.85"}
            resp = client.post("/api/product/identify", files=files, data=data)
        t_total = time.perf_counter() - t0
        print(f"Status: {resp.status_code} | Total HTTP Roundtrip: {t_total:.4f}s")
        if resp.status_code != 200:
            print("Response error:", resp.text)

    print("\n" + "=" * 80)
    print("RAW COLLECTED TIMINGS (SECONDS)")
    print("=" * 80)
    for k, v in collector.items():
        print(f"{k}: {[round(x, 4) for x in v]}")

    # Aggregate Q&A LLM calls (routing + answer generation)
    qa_llm_combined = []
    qa_routing = collector.get("qa:llm_call_routing", [])
    qa_answer = collector.get("qa:llm_call_answer", [])
    for r, a in zip(qa_routing, qa_answer):
        qa_llm_combined.append(r + a)

    print("\n" + "=" * 80)
    print("SUMMARY LATENCY TABLES")
    print("=" * 80)

    def print_stage_stats(title, stages_dict):
        print(f"\n### {title}")
        print("| Stage | Min (s) | Median (s) | Max (s) |")
        print("|---|---|---|---|")
        for stage_name, vals in stages_dict.items():
            if not vals:
                print(f"| {stage_name} | N/A | N/A | N/A |")
            else:
                s_min = f"{min(vals):.4f}"
                s_med = f"{statistics.median(vals):.4f}"
                s_max = f"{max(vals):.4f}"
                print(f"| {stage_name} | {s_min} | {s_med} | {s_max} |")

    qa_stages = {
        "Request parse": collector.get("qa:request_parse", []),
        "Image fetch": [],
        "CLIP embedding": [],
        "AI Search query": collector.get("qa:ai_search_query", []),
        "LLM call (tool routing)": qa_routing,
        "LLM call (answer generation)": qa_answer,
        "LLM call (total)": qa_llm_combined if qa_llm_combined else collector.get("qa:llm_call_answer", []),
        "Response serialization": collector.get("qa:response_serialization", []),
    }
    print_stage_stats("Q&A Endpoint (/api/agent/query)", qa_stages)

    identify_stages = {
        "Request parse": collector.get("identify:request_parse", []),
        "Image fetch": collector.get("identify:image_fetch", []),
        "CLIP embedding": collector.get("identify:clip_embedding", []),
        "AI Search query": collector.get("identify:ai_search_query", []),
        "LLM call (Open-World Vision)": collector.get("identify:llm_call", []),
        "Response serialization": collector.get("identify:response_serialization", []),
    }
    print_stage_stats("Identify Endpoint (/api/product/identify)", identify_stages)


if __name__ == "__main__":
    main()
