"""VisionIQ Pipeline Latency Diagnostic Suite.

Measures exact millisecond latency across:
1. Tool Selection LLM call (Azure OpenAI Foundry Agent)
2. Azure AI Search Query (Vector Search & Doc Lookup)
3. Open-World Image Identification LLM Call (Vision Model)
4. CLIP ViT-B/32 Image Embedding & Normalization
5. Answer Generation Grounded LLM Call
6. Video Search & Grounded Video QA
7. Video Cache Verification (Cold vs Warm)
"""

import json
import logging
import os
from pathlib import Path
import sys
import time

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
for directory in (str(ROOT_DIR), str(ROOT_DIR / "backend")):
    if directory not in sys.path:
        sys.path.insert(0, directory)

from backend.config import settings
from services.llm import get_azure_openai_client, generate_grounded_answer
from agent.agent import VisionIQAgent, FOUNDRY_TOOL_DEFINITIONS
from agent.prompts import SYSTEM_PROMPT
from services.product_search.embeddings import generate_image_embedding
from services.product_search.matcher import identify_product as match_product_catalog, get_search_client
from services.rag.rag_service import retrieve_product_by_id, answer_product_question
from services.video.search import search_video_segments, grounded_video_qa
from services.vision.open_world_identifier import identify_product_open_world

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("diagnose")


def time_block(label: str):
    """Context manager to measure elapsed time in milliseconds."""
    class TimerContext:
        def __enter__(self):
            self.start = time.perf_counter()
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.elapsed_ms = (time.perf_counter() - self.start) * 1000.0
    return TimerContext()


def run_latency_diagnostics():
    print("=" * 80)
    print("VISIONIQ PIPELINE STEP-BY-STEP LATENCY & TOKEN DIAGNOSTICS")
    print("=" * 80)

    timing_results = {}

    # ------------------------------------------------------------------------
    # 1. TOOL SELECTION LLM CALL
    # ------------------------------------------------------------------------
    print("\n[1/6] Measuring Tool Selection LLM Call (Foundry Agent)...")
    agent = VisionIQAgent()
    client = get_azure_openai_client()
    deployment = settings.AZURE_OPENAI_DEPLOYMENT_NAME

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "[Context: Product ID is P001] What is the battery life of this product?"},
    ]

    t0 = time.perf_counter()
    resp1 = client.chat.completions.create(
        model=deployment,
        messages=messages,
        tools=FOUNDRY_TOOL_DEFINITIONS,
        tool_choice="auto",
        max_completion_tokens=300,
    )
    t1 = time.perf_counter()
    tool_sel_ms = (t1 - t0) * 1000.0
    u1 = resp1.usage
    timing_results["tool_selection_llm"] = {
        "latency_ms": round(tool_sel_ms, 2),
        "deployment": deployment,
        "max_completion_tokens_param": 300,
        "actual_prompt_tokens": u1.prompt_tokens if u1 else "N/A",
        "actual_completion_tokens": u1.completion_tokens if u1 else "N/A",
        "selected_tool": resp1.choices[0].message.tool_calls[0].function.name if resp1.choices[0].message.tool_calls else "None",
    }
    print(f"   -> Latency: {tool_sel_ms:.2f} ms | Selected: {timing_results['tool_selection_llm']['selected_tool']} | Tokens: {timing_results['tool_selection_llm']['actual_completion_tokens']}")

    # ------------------------------------------------------------------------
    # 2. AZURE AI SEARCH QUERIES
    # ------------------------------------------------------------------------
    print("\n[2/6] Measuring Azure AI Search Vector & Doc Queries...")
    
    # Direct Key Lookup
    t0 = time.perf_counter()
    doc = retrieve_product_by_id("P001")
    t1 = time.perf_counter()
    doc_lookup_ms = (t1 - t0) * 1000.0
    timing_results["azure_search_doc_lookup"] = {
        "latency_ms": round(doc_lookup_ms, 2),
        "found": doc is not None,
        "product_name": doc.get("name") if doc else "N/A",
    }
    print(f"   -> Direct Doc Lookup (P001): {doc_lookup_ms:.2f} ms | Found: {doc is not None}")

    # Vector Search query
    sample_img_url = "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&q=80"
    t0 = time.perf_counter()
    vec = generate_image_embedding(sample_img_url)
    t1 = time.perf_counter()
    clip_embed_ms = (t1 - t0) * 1000.0
    timing_results["clip_embedding_generation"] = {
        "latency_ms": round(clip_embed_ms, 2),
        "dim": len(vec),
    }
    t0 = time.perf_counter()
    vec_warm = generate_image_embedding(sample_img_url)
    t1 = time.perf_counter()
    clip_warm_ms = (t1 - t0) * 1000.0
    timing_results["clip_embedding_generation_warm"] = {
        "latency_ms": round(clip_warm_ms, 2),
        "dim": len(vec_warm),
    }
    print(f"   -> CLIP Image Vectorization (Warm Cache): {clip_warm_ms:.2f} ms")

    t0 = time.perf_counter()
    catalog_matches = match_product_catalog(image=sample_img_url, top_k=3)
    t1 = time.perf_counter()
    catalog_match_ms = (t1 - t0) * 1000.0
    timing_results["product_catalog_vector_search"] = {
        "latency_ms": round(catalog_match_ms, 2),
        "match_count": len(catalog_matches),
    }
    print(f"   -> Azure AI Search Vector Query: {catalog_match_ms:.2f} ms | Candidates: {len(catalog_matches)}")

    # ------------------------------------------------------------------------
    # 3. ANSWER GENERATION GROUNDED LLM CALL
    # ------------------------------------------------------------------------
    print("\n[3/6] Measuring Answer Generation LLM Call (Grounded QA)...")
    context = (
        "Product: Sony WH-1000XM5\n"
        "Brand: Sony\n"
        "Category: Headphones\n"
        "Specifications:\n"
        "- Battery Life: 30 hours with ANC on, up to 40 hours with ANC off\n"
        "- Noise Cancellation: Dual Processor V1 and HD Noise Canceling Processor QN1\n"
    )
    t0 = time.perf_counter()
    ans = generate_grounded_answer(
        user_question="What is the battery life?",
        retrieved_context=context,
    )
    t1 = time.perf_counter()
    answer_gen_ms = (t1 - t0) * 1000.0
    timing_results["grounded_answer_llm"] = {
        "latency_ms": round(answer_gen_ms, 2),
        "max_completion_tokens_param": 2500,
        "answer_preview": ans[:80] + "..." if len(ans) > 80 else ans,
    }
    print(f"   -> Latency: {answer_gen_ms:.2f} ms | Answer: {timing_results['grounded_answer_llm']['answer_preview']}")

    # ------------------------------------------------------------------------
    # 4. OPEN-WORLD MULTIMODAL VISION LLM CALL
    # ------------------------------------------------------------------------
    print("\n[4/6] Measuring Open-World Vision LLM Call (Image + Prompt)...")
    t0 = time.perf_counter()
    ow_result = identify_product_open_world(image=sample_img_url)
    t1 = time.perf_counter()
    open_world_ms = (t1 - t0) * 1000.0
    timing_results["open_world_vision_llm"] = {
        "latency_ms": round(open_world_ms, 2),
        "max_completion_tokens_param": 800,
        "identified_product": ow_result.get("product_name"),
        "identified_brand": ow_result.get("brand"),
    }
    print(f"   -> Latency: {open_world_ms:.2f} ms | Product: {ow_result.get('product_name')} ({ow_result.get('brand')})")

    # ------------------------------------------------------------------------
    # 5. VIDEO RETRIEVAL & GROUNDED QA
    # ------------------------------------------------------------------------
    print("\n[5/6] Measuring Video Search & Grounded Video QA...")
    cached_video_id = "vid_df16da8f30f96fb6"
    t0 = time.perf_counter()
    v_matches = search_video_segments(video_id=cached_video_id, query="What is discussed regarding battery?", top_k=3)
    t1 = time.perf_counter()
    video_search_ms = (t1 - t0) * 1000.0
    timing_results["video_search_segments"] = {
        "latency_ms": round(video_search_ms, 2),
        "match_count": len(v_matches),
    }
    print(f"   -> Video Vector Search (Azure AI Search): {video_search_ms:.2f} ms | Matches: {len(v_matches)}")

    t0 = time.perf_counter()
    v_qa = grounded_video_qa(video_id=cached_video_id, question="What is discussed regarding battery life?")
    t1 = time.perf_counter()
    video_qa_ms = (t1 - t0) * 1000.0
    timing_results["video_grounded_qa_end_to_end"] = {
        "latency_ms": round(video_qa_ms, 2),
        "found_match": v_qa.get("found_match"),
        "answer_preview": v_qa.get("answer", "")[:80] + "...",
    }
    print(f"   -> End-to-End Video QA: {video_qa_ms:.2f} ms | Answer: {timing_results['video_grounded_qa_end_to_end']['answer_preview']}")

    # ------------------------------------------------------------------------
    # 6. VIDEO TRANSCRIPTION / CACHE CHECK
    # ------------------------------------------------------------------------
    print("\n[6/6] Checking Video Cache Status...")
    cache_dir = ROOT_DIR / "data" / "cache" / "video_analysis"
    cached_files = list(cache_dir.glob("*.json"))
    timing_results["video_cache"] = {
        "cache_directory": str(cache_dir),
        "cached_videos_count": len(cached_files),
        "cached_video_ids": [f.stem for f in cached_files],
    }
    print(f"   -> Found {len(cached_files)} cached video analyses in disk cache: {[f.stem for f in cached_files]}")

    # ------------------------------------------------------------------------
    # FULL END-TO-END AGENT QUERY
    # ------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("MEASURING FULL END-TO-END AGENT QUERY VIA agent.run()")
    print("=" * 80)
    
    t0 = time.perf_counter()
    agent_result = agent.run(
        user_prompt="What is the battery life of this headphone?",
        product_id="P001",
    )
    t1 = time.perf_counter()
    e2e_agent_ms = (t1 - t0) * 1000.0
    timing_results["full_e2e_agent_query"] = {
        "latency_ms": round(e2e_agent_ms, 2),
        "selected_tool": agent_result.get("selected_tool"),
    }
    print(f"   -> Full Agent.run() Execution: {e2e_agent_ms:.2f} ms ({e2e_agent_ms / 1000.0:.2f} s)")

    print("\n" + "=" * 80)
    print("FINAL SUMMARY BREAKDOWN")
    print("=" * 80)
    print(json.dumps(timing_results, indent=2))
    return timing_results


if __name__ == "__main__":
    run_latency_diagnostics()
