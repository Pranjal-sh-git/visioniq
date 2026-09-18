"""Test script for Open-World Product Identification & Catalog Recommendations."""

import sys
import os
import io
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from services.vision.open_world_identifier import identify_product_open_world
from services.product_search.matcher import find_similar_catalog_products


def test_sony_headphone_photo():
    print("=" * 80)
    print("TEST 1: Real User Photo of Sony Headphones (Pink/Pastel)")
    print("=" * 80)
    
    img_path = Path("data/uploads/images/61wSmw6oC7L._AC_.jpg")
    if not img_path.exists():
        print(f"Skipping test 1: Image not found at {img_path}")
        return

    # Step 1: Open-World Vision AI
    print("\n[Step 1] Running identify_product_open_world()...")
    open_world_result = identify_product_open_world(image=img_path)
    print(f"  Brand:                 {open_world_result.get('brand')}")
    print(f"  Model:                 {open_world_result.get('model')}")
    print(f"  Product Name:          {open_world_result.get('product_name')}")
    print(f"  Category:              {open_world_result.get('category')}")
    print(f"  Confidence:            {open_world_result.get('confidence')}")
    print(f"  Visual Description:    {open_world_result.get('visual_description')}")
    print(f"  Observed Features:     {open_world_result.get('key_features_observed')}")

    # Assert that it identifies Sony (NOT AirPods Max!)
    brand_lower = (open_world_result.get("brand") or "").lower()
    name_lower = (open_world_result.get("product_name") or "").lower()
    assert "sony" in brand_lower or "sony" in name_lower, (
        f"Expected Sony identification, got brand='{open_world_result.get('brand')}', name='{open_world_result.get('product_name')}'"
    )
    print("\n  >>> PASSED: Accurately recognized as SONY headphones! (No closed-set AirPods misclassification)")

    # Step 2: Catalog recommendations
    print("\n[Step 2] Running find_similar_catalog_products()...")
    similar_items = find_similar_catalog_products(image=img_path, identified_info=open_world_result, top_k=3)
    print(f"  Found {len(similar_items)} catalog recommendations:")
    for idx, item in enumerate(similar_items, 1):
        print(f"    {idx}. [{item.get('id')}] {item.get('brand')} {item.get('name')} (Similarity: {item.get('similarity_score')})")
        print(f"       Category: {item.get('category')}")
        print(f"       Reason: {item.get('recommendation_reason')}")


def test_catalog_sample_image():
    print("\n" + "=" * 80)
    print("TEST 2: Catalog Sony WH-1000XM5 Image URL")
    print("=" * 80)

    url = "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=800&q=80"
    print("\n[Step 1] Running identify_product_open_world() on URL...")
    open_world_result = identify_product_open_world(image_url=url)
    print(f"  Brand:                 {open_world_result.get('brand')}")
    print(f"  Product Name:          {open_world_result.get('product_name')}")
    print(f"  Category:              {open_world_result.get('category')}")
    print(f"  Confidence:            {open_world_result.get('confidence')}")

    print("\n[Step 2] Running find_similar_catalog_products()...")
    similar_items = find_similar_catalog_products(image=url, identified_info=open_world_result, top_k=3)
    for idx, item in enumerate(similar_items, 1):
        print(f"    {idx}. [{item.get('id')}] {item.get('brand')} {item.get('name')} (Score: {item.get('similarity_score')}, ExactMatch: {item.get('is_exact_catalog_match')})")


if __name__ == "__main__":
    test_sony_headphone_photo()
    test_catalog_sample_image()
    print("\n" + "=" * 80)
    print("ALL OPEN-WORLD TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 80)
