"""Investigation script for real-world product image matching vs catalog indexing."""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from services.product_search.matcher import identify_product, DEFAULT_CONFIDENCE_THRESHOLD, get_search_client
from services.product_search.embeddings import generate_image_embedding
from azure.search.documents.models import VectorizedQuery

# Real-world test images (different angles, real backgrounds, lighting)
TEST_IMAGES = [
    {
        "label": "Sony WH-1000XM5 (Real user photo on table/desk)",
        "ground_truth_id": "P001",
        "ground_truth_name": "Sony WH-1000XM5",
        "url": "https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?auto=format&fit=crop&w=800&q=80"
    },
    {
        "label": "Sony WH-1000XM5 (Worn by person / lifestyle angle)",
        "ground_truth_id": "P001",
        "ground_truth_name": "Sony WH-1000XM5",
        "url": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?auto=format&fit=crop&w=800&q=80"
    },
    {
        "label": "Apple AirPods Max (Real desk photo with shadows)",
        "ground_truth_id": "P003",
        "ground_truth_name": "Apple AirPods Max",
        "url": "https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?auto=format&fit=crop&w=800&q=80"
    },
    {
        "label": "Office Ergonomic Chair (Real room photo)",
        "ground_truth_id": "P006",
        "ground_truth_name": "Herman Miller Aeron",
        "url": "https://images.unsplash.com/photo-1505797149-43b0069ec26b?auto=format&fit=crop&w=800&q=80"
    },
    {
        "label": "Nike Running Shoes (Real outdoor street photo)",
        "ground_truth_id": "P011",
        "ground_truth_name": "Nike Air Zoom Pegasus 40",
        "url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80"
    }
]

def run_investigation():
    print("=" * 90)
    print("INVESTIGATION: Product Matching Behavior on Real-World Photos")
    print(f"Default Confidence Threshold: {DEFAULT_CONFIDENCE_THRESHOLD}")
    print("=" * 90)

    # 1. Check products.json for AirPods Max
    products_path = BASE_DIR / "data" / "products" / "products.json"
    with open(products_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    airpods_entry = next((p for p in products if "airpods" in p.get("name", "").lower() or "airpods" in p.get("brand", "").lower()), None)
    print(f"\n[PART 1] Does 'AirPods Max' exist in products.json?")
    if airpods_entry:
        print(f"-> YES. Found catalog entry:")
        print(f"   ID: {airpods_entry.get('id')}")
        print(f"   Brand: {airpods_entry.get('brand')}")
        print(f"   Name: {airpods_entry.get('name')}")
        print(f"   Category: {airpods_entry.get('category')}")
        print(f"   Image URLs: {airpods_entry.get('image_urls')}")
    else:
        print("-> NO. AirPods Max does not exist in products.json")

    # 2. Test Real-World Photos
    print("\n" + "=" * 90)
    print("[PART 2, 3, 4] Running identify_product() on Real-World Images & Inspecting All Candidates")
    print("=" * 90)

    for i, test in enumerate(TEST_IMAGES, 1):
        print(f"\n--- Test Image {i}: {test['label']} ---")
        print(f"URL: {test['url']}")
        print(f"Expected Ground Truth: [{test['ground_truth_id']}] {test['ground_truth_name']}")

        try:
            # Query top-5 to see full spectrum of scores
            results = identify_product(test['url'], top_k=5, confidence_threshold=DEFAULT_CONFIDENCE_THRESHOLD)
            
            print(f"\nTop-5 Candidates from Azure AI Search:")
            for rank, match in enumerate(results, 1):
                is_best = (rank == 1)
                is_gt = (match['id'] == test['ground_truth_id'])
                flag_gt = " <-- [EXPECTED GROUND TRUTH]" if is_gt else ""
                print(f"  #{rank}: [{match['id']}] {match['brand']} {match['name']}")
                print(f"      Similarity Score (@search.score): {match['similarity_score']:.4f}")
                print(f"      True Cosine Similarity: {2 * match['similarity_score'] - 1:.4f}")
                print(f"      Is Confident Match (score >= {DEFAULT_CONFIDENCE_THRESHOLD}): {match['is_confident_match']}")
                print(f"      Match Status: {match['match_status']}{flag_gt}")

            top_1 = results[0] if results else None
            if top_1:
                print(f"\nSummary for Test Image {i}:")
                print(f"  Top-1 Match ID: {top_1['id']} ({top_1['brand']} {top_1['name']})")
                print(f"  Top-1 Score: {top_1['similarity_score']:.4f}")
                print(f"  Correct Product at Rank 1? {top_1['id'] == test['ground_truth_id']}")
                print(f"  Did confidence filter mark it confident? {top_1['is_confident_match']}")
                if not top_1['is_confident_match']:
                    print(f"  -> System appropriately returned 'no_confident_match' (score {top_1['similarity_score']:.4f} < {DEFAULT_CONFIDENCE_THRESHOLD})")
                else:
                    print(f"  -> System accepted match as confident (score {top_1['similarity_score']:.4f} >= {DEFAULT_CONFIDENCE_THRESHOLD})")
        except Exception as e:
            print(f"  ERROR testing image: {e}")

if __name__ == "__main__":
    run_investigation()
