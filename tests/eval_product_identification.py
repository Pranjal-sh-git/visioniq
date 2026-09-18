"""Product Identification Evaluation Script (Day 4 Benchmark).

Evaluates 25 product images (in-catalog known items, varied angles, and out-of-catalog items)
against the Azure AI Search vector catalog to measure Top-1, Top-3 accuracy, latency, and failure rate.
Outputs real computed results to CSV and Markdown in data/evaluation/.
"""

import csv
import json
import logging
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from services.product_search.matcher import identify_product, DEFAULT_CONFIDENCE_THRESHOLD

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("eval_products")

EVAL_DIR = BASE_DIR / "data" / "evaluation"
EVAL_DIR.mkdir(parents=True, exist_ok=True)

# 25 Curated Evaluation Test Cases
PRODUCT_EVAL_DATASET = [
    # Headphones Category (In-Catalog)
    {"test_id": "T01", "name": "Sony WH-1000XM5 (Catalog Photo)", "gt_id": "P001", "category": "Headphones", "is_in_catalog": True, "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=800&q=80"},
    {"test_id": "T02", "name": "Sony WH-1000XM5 (Secondary Angle)", "gt_id": "P001", "category": "Headphones", "is_in_catalog": True, "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=800&q=80"},
    {"test_id": "T03", "name": "Bose QuietComfort Ultra", "gt_id": "P002", "category": "Headphones", "is_in_catalog": True, "image_url": "https://images.unsplash.com/photo-1583394838336-acd977736f90?auto=format&fit=crop&w=800&q=80"},
    {"test_id": "T04", "name": "Apple AirPods Max", "gt_id": "P003", "category": "Headphones", "is_in_catalog": True, "image_url": "https://images.unsplash.com/photo-1545127398-14699f92334b?auto=format&fit=crop&w=800&q=80"},
    {"test_id": "T05", "name": "Sennheiser Momentum 4", "gt_id": "P004", "category": "Headphones", "is_in_catalog": True, "image_url": "https://images.unsplash.com/photo-1484704849700-f032a568e944?auto=format&fit=crop&w=800&q=80"},
    {"test_id": "T06", "name": "Audio-Technica ATH-M50xBT2", "gt_id": "P005", "category": "Headphones", "is_in_catalog": True, "image_url": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?auto=format&fit=crop&w=800&q=80"},
    {"test_id": "T07", "name": "Bowers & Wilkins Px7 S2e", "gt_id": "P006", "category": "Headphones", "is_in_catalog": True, "image_url": "https://images.unsplash.com/photo-1524678606370-a47ad25cb82a?auto=format&fit=crop&w=800&q=80"},

    # Office Chairs Category (In-Catalog)
    {"test_id": "T08", "name": "Herman Miller Aeron Chair", "gt_id": "P007", "category": "Chairs", "is_in_catalog": True, "image_url": "https://images.unsplash.com/photo-1589384267710-7a170981ca78?auto=format&fit=crop&w=800&q=80"},
    {"test_id": "T09", "name": "Steelcase Gesture", "gt_id": "P008", "category": "Chairs", "is_in_catalog": True, "image_url": "https://images.unsplash.com/photo-1505797149-43b0069ec26b?auto=format&fit=crop&w=800&q=80"},
    {"test_id": "T10", "name": "Secretlab Titan Evo", "gt_id": "P009", "category": "Chairs", "is_in_catalog": True, "image_url": "https://images.unsplash.com/photo-1598550476439-6847785fcea6?auto=format&fit=crop&w=800&q=80"},
    {"test_id": "T11", "name": "Autonomous ErgoChair Pro", "gt_id": "P010", "category": "Chairs", "is_in_catalog": True, "image_url": "https://images.unsplash.com/photo-1616046229478-9901c5536a45?auto=format&fit=crop&w=800&q=80"},
    {"test_id": "T12", "name": "Haworth Fern Chair", "gt_id": "P012", "category": "Chairs", "is_in_catalog": True, "image_url": "https://images.unsplash.com/photo-1567538096630-e0c55bd6374c?auto=format&fit=crop&w=800&q=80"},
    {"test_id": "T13", "name": "Humanscale Freedom Chair", "gt_id": "P013", "category": "Chairs", "is_in_catalog": True, "image_url": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?auto=format&fit=crop&w=800&q=80"},

    # Running Shoes Category (In-Catalog)
    {"test_id": "T14", "name": "Nike Air Zoom Pegasus 40", "gt_id": "P011", "category": "Shoes", "is_in_catalog": True, "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80"},
    {"test_id": "T15", "name": "Nike Air Max 270", "gt_id": "P014", "category": "Shoes", "is_in_catalog": True, "image_url": "https://images.unsplash.com/photo-1514989940723-e8e51635b782?auto=format&fit=crop&w=800&q=80"},
    {"test_id": "T16", "name": "Adidas Ultraboost Light", "gt_id": "P015", "category": "Shoes", "is_in_catalog": True, "image_url": "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?auto=format&fit=crop&w=800&q=80"},
    {"test_id": "T17", "name": "New Balance 990v6", "gt_id": "P016", "category": "Shoes", "is_in_catalog": True, "image_url": "https://images.unsplash.com/photo-1551107696-a4b0c5a0d9a2?auto=format&fit=crop&w=800&q=80"},
    {"test_id": "T18", "name": "On Running Cloudmonster", "gt_id": "P017", "category": "Shoes", "is_in_catalog": True, "image_url": "https://images.unsplash.com/photo-1608231387042-66d1773070a5?auto=format&fit=crop&w=800&q=80"},
    {"test_id": "T19", "name": "Hoka Clifton 9", "gt_id": "P018", "category": "Shoes", "is_in_catalog": True, "image_url": "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?auto=format&fit=crop&w=800&q=80"},
    {"test_id": "T20", "name": "Salomon XT-6", "gt_id": "P019", "category": "Shoes", "is_in_catalog": True, "image_url": "https://images.unsplash.com/photo-1539185441755-769473a23570?auto=format&fit=crop&w=800&q=80"},

    # Out-of-Catalog / Unknown / Negative Control Items
    {"test_id": "T21", "name": "Mechanical Keyboard (Out-of-Catalog)", "gt_id": None, "category": "Keyboards", "is_in_catalog": False, "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=800&q=80"},
    {"test_id": "T22", "name": "Coffee Espresso Machine (Out-of-Catalog)", "gt_id": None, "category": "Appliances", "is_in_catalog": False, "image_url": "https://images.unsplash.com/photo-1517668808822-9ebb02f2a0e6?auto=format&fit=crop&w=800&q=80"},
    {"test_id": "T23", "name": "DSLR Camera Lens (Out-of-Catalog)", "gt_id": None, "category": "Cameras", "is_in_catalog": False, "image_url": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=800&q=80"},
    {"test_id": "T24", "name": "Ceramic Coffee Mug (Out-of-Catalog)", "gt_id": None, "category": "Kitchen", "is_in_catalog": False, "image_url": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=800&q=80"},
    {"test_id": "T25", "name": "Bicycle Road Frame (Out-of-Catalog)", "gt_id": None, "category": "Sports", "is_in_catalog": False, "image_url": "https://images.unsplash.com/photo-1485965120184-e220f721d03e?auto=format&fit=crop&w=800&q=80"},
]


def run_product_evaluation():
    print("=" * 90)
    print("VISIONIQ — DAY 4 EVALUATION: PRODUCT IDENTIFICATION BENCHMARK (25 TEST CASES)")
    print("=" * 90)

    results = []
    top1_hits = 0
    top3_hits = 0
    in_catalog_count = 0
    out_catalog_correct_unconfident = 0
    out_catalog_count = 0
    latencies = []
    failures = 0

    for idx, item in enumerate(PRODUCT_EVAL_DATASET, 1):
        test_id = item["test_id"]
        test_name = item["name"]
        gt_id = item["gt_id"]
        is_in_cat = item["is_in_catalog"]
        img_url = item["image_url"]

        if is_in_cat:
            in_catalog_count += 1
        else:
            out_catalog_count += 1

        print(f"\n[{idx}/25] Evaluating: {test_id} - {test_name} (Expected GT: {gt_id or 'NONE [Out-of-Catalog]'})")

        start_time = time.perf_counter()
        try:
            matches = identify_product(image=img_url, top_k=3, confidence_threshold=DEFAULT_CONFIDENCE_THRESHOLD)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            latencies.append(latency_ms)

            rank1 = matches[0] if len(matches) > 0 else {}
            rank2 = matches[1] if len(matches) > 1 else {}
            rank3 = matches[2] if len(matches) > 2 else {}

            candidate_ids = [m.get("id") for m in matches]
            top1_id = rank1.get("id")
            top1_score = rank1.get("similarity_score", 0.0)
            top1_name = f"{rank1.get('brand', '')} {rank1.get('name', '')}".strip()
            is_confident = rank1.get("is_confident_match", False)

            # Accuracy Computations
            is_top1_correct = (top1_id == gt_id) if is_in_cat else False
            is_top3_correct = (gt_id in candidate_ids) if is_in_cat else False

            if is_in_cat:
                if is_top1_correct:
                    top1_hits += 1
                if is_top3_correct:
                    top3_hits += 1
            else:
                # For out-of-catalog items, success means NOT confident (score < 0.85)
                if not is_confident or top1_score < DEFAULT_CONFIDENCE_THRESHOLD:
                    out_catalog_correct_unconfident += 1

            eval_row = {
                "test_id": test_id,
                "test_name": test_name,
                "ground_truth_id": gt_id or "OUT_OF_CATALOG",
                "in_catalog": is_in_cat,
                "top1_id": top1_id,
                "top1_name": top1_name,
                "top1_score": top1_score,
                "top2_id": rank2.get("id", ""),
                "top2_score": rank2.get("similarity_score", 0.0),
                "top3_id": rank3.get("id", ""),
                "top3_score": rank3.get("similarity_score", 0.0),
                "top1_hit": is_top1_correct,
                "top3_hit": is_top3_correct,
                "is_confident_match": is_confident,
                "latency_ms": latency_ms,
                "status": "SUCCESS"
            }

            print(f"    Rank 1: [{top1_id}] {top1_name} (Score: {top1_score:.4f} | Confident: {is_confident})")
            print(f"    Top-1 Hit: {is_top1_correct} | Top-3 Hit: {is_top3_correct} | Latency: {latency_ms}ms")
            results.append(eval_row)

        except Exception as e:
            logger.exception(f"Error evaluating test {test_id}: {e}")
            failures += 1
            results.append({
                "test_id": test_id,
                "test_name": test_name,
                "ground_truth_id": gt_id or "OUT_OF_CATALOG",
                "in_catalog": is_in_cat,
                "top1_id": "ERROR",
                "top1_name": str(e),
                "top1_score": 0.0,
                "top2_id": "",
                "top2_score": 0.0,
                "top3_id": "",
                "top3_score": 0.0,
                "top1_hit": False,
                "top3_hit": False,
                "is_confident_match": False,
                "latency_ms": 0.0,
                "status": "FAILED"
            })

    # Summary Statistics
    total_tests = len(PRODUCT_EVAL_DATASET)
    top1_acc = round((top1_hits / in_catalog_count) * 100, 2) if in_catalog_count else 0.0
    top3_acc = round((top3_hits / in_catalog_count) * 100, 2) if in_catalog_count else 0.0
    out_cat_rej_acc = round((out_catalog_correct_unconfident / out_catalog_count) * 100, 2) if out_catalog_count else 0.0
    avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
    failure_rate = round((failures / total_tests) * 100, 2)

    print("\n" + "=" * 90)
    print("PRODUCT IDENTIFICATION BENCHMARK SUMMARY (COMPUTED LIVE)")
    print("=" * 90)
    print(f"Total Test Images: {total_tests}")
    print(f"In-Catalog Tests: {in_catalog_count} | Out-of-Catalog Tests: {out_catalog_count}")
    print(f"Top-1 Accuracy (In-Catalog): {top1_hits}/{in_catalog_count} ({top1_acc}%)")
    print(f"Top-3 Accuracy (In-Catalog): {top3_hits}/{in_catalog_count} ({top3_acc}%)")
    print(f"Out-of-Catalog Graceful Rejection: {out_catalog_correct_unconfident}/{out_catalog_count} ({out_cat_rej_acc}%)")
    print(f"Average Response Time: {avg_latency} ms")
    print(f"Failure Rate: {failures}/{total_tests} ({failure_rate}%)")
    print("=" * 90)

    # Save to CSV
    csv_file = EVAL_DIR / "product_identification_eval.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    print(f"\n[OUTPUT] Saved detailed CSV to: {csv_file}")

    # Save to Markdown
    md_file = EVAL_DIR / "product_identification_eval.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write("# Product Identification Evaluation Benchmark (Day 4)\n\n")
        f.write(f"**Execution Date**: 2026-09-17 | **Model**: OpenAI CLIP (`clip-ViT-B-32`) | **Index**: Azure AI Search `product-catalog`\n\n")
        f.write("## Executive Metrics\n\n")
        f.write(f"- **Top-1 Accuracy (In-Catalog)**: **{top1_acc}%** ({top1_hits}/{in_catalog_count})\n")
        f.write(f"- **Top-3 Accuracy (In-Catalog)**: **{top3_acc}%** ({top3_hits}/{in_catalog_count})\n")
        f.write(f"- **Out-of-Catalog Rejection Rate**: **{out_cat_rej_acc}%** ({out_catalog_correct_unconfident}/{out_catalog_count})\n")
        f.write(f"- **Mean Response Latency**: **{avg_latency} ms**\n")
        f.write(f"- **Failure / Error Rate**: **{failure_rate}%**\n\n")
        f.write("## Detailed Per-Image Evaluation Results\n\n")
        f.write("| Test ID | Test Image Description | Expected GT | Top-1 Match | Top-1 Score | Top-1 Hit | Top-3 Hit | Confident? | Latency (ms) |\n")
        f.write("| :---: | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: |\n")
        for r in results:
            t1_hit_sym = "✅" if r["top1_hit"] else ("❌" if r["in_catalog"] else "—")
            t3_hit_sym = "✅" if r["top3_hit"] else ("❌" if r["in_catalog"] else "—")
            conf_sym = "✅ True" if r["is_confident_match"] else "○ False"
            f.write(f"| {r['test_id']} | {r['test_name']} | `{r['ground_truth_id']}` | [{r['top1_id']}] {r['top1_name']} | {r['top1_score']:.4f} | {t1_hit_sym} | {t3_hit_sym} | {conf_sym} | {r['latency_ms']} ms |\n")
    print(f"[OUTPUT] Saved detailed Markdown to: {md_file}")

    return {
        "top1_acc": top1_acc,
        "top3_acc": top3_acc,
        "out_cat_rej_acc": out_cat_rej_acc,
        "avg_latency": avg_latency,
        "failure_rate": failure_rate,
    }


if __name__ == "__main__":
    run_product_evaluation()
