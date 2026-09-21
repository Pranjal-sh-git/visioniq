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



def test_sony_followup_buying_link():
    print("\n" + "=" * 80)
    print("TEST 3: Follow-Up Question ('can i get the buying link') on Open-World Sony Headphones")
    print("=" * 80)

    from agent.agent import VisionIQAgent
    agent = VisionIQAgent()

    sony_info = {
        "product_name": "Sony wireless over-ear headphones (pink)",
        "brand": "Sony",
        "category": "Headphones",
        "visual_description": "Pink wireless over-ear headphones with soft cushioned earcups and Sony branding.",
    }

    # User asks "can i get the buying link" without clicking any similar-product card
    result = agent.run(
        user_prompt="can i get the buying link",
        product_id=None,
        product_info=sony_info,
    )

    print(f"  Selected Tool:     {result.get('selected_tool')}")
    print(f"  Tool Parameters:   {result.get('tool_parameters')}")
    print(f"  Routing Reasoning: {result.get('routing_reasoning')}")
    
    tool_output = result.get("tool_output", {})
    answer = tool_output.get("answer", "")
    print(f"\n  Chatbot Answer:\n{answer}\n")

    # Assertions
    assert result.get("selected_tool") == "search_product_knowledge", f"Expected search_product_knowledge, got {result.get('selected_tool')}"
    assert "airpods" not in answer.lower(), f"Bug detected: Chatbot answered about AirPods Max: {answer}"
    assert "p003" not in answer.lower(), f"Bug detected: Chatbot answered about P003: {answer}"
    assert "sony" in answer.lower() or "pink" in answer.lower(), f"Answer does not ground on Sony pink headphones: {answer}"
    print("  >>> PASSED: Chatbot answered regarding Sony pink headphones and did NOT leak AirPods Max (P003)!")


def test_non_catalog_category_smartphone():
    print("\n" + "=" * 80)
    print("TEST 4: Category Relevance Check for Non-Catalog Item (iPhone / Smartphone)")
    print("=" * 80)

    iphone_info = {
        "brand": "Apple",
        "model": "iPhone 15 Pro",
        "product_name": "Apple iPhone 15 Pro",
        "category": "Electronics/Smartphone",
        "visual_description": "Titanium finish smartphone with triple camera system on the rear.",
        "confidence": "high",
        "key_features_observed": ["Triple camera array", "Titanium frame", "OLED display"],
    }

    # Calling find_similar_catalog_products with an image URL or direct info
    iphone_sample_url = "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?auto=format&fit=crop&w=800&q=80"
    similar_items = find_similar_catalog_products(
        image=iphone_sample_url,
        identified_info=iphone_info,
        top_k=3,
    )

    print(f"  Similar catalog recommendations returned: {len(similar_items)}")
    for item in similar_items:
        print(f"    - [{item.get('id')}] {item.get('brand')} {item.get('name')} ({item.get('category')})")

    # Assert that NO misleading catalog items (headphones/watches/chairs) are returned
    assert len(similar_items) == 0, (
        f"Expected 0 recommendations for non-catalog category 'Smartphone', but got {len(similar_items)} items!"
    )
    print("  >>> PASSED: Successfully suppressed catalog recommendations for out-of-catalog smartphone category!")


def test_in_catalog_category_shoe():
    print("\n" + "=" * 80)
    print("TEST 5: In-Catalog Item Category Relevance Check (Nike Shoe)")
    print("=" * 80)

    shoe_info = {
        "brand": "Nike",
        "model": "Air Zoom Pegasus",
        "product_name": "Nike Air Zoom Pegasus Running Shoes",
        "category": "Footwear",
        "visual_description": "Athletic running shoes with red engineered mesh upper and responsive foam midsole.",
        "confidence": "high",
        "key_features_observed": ["Engineered mesh upper", "Foam midsole", "Rubber outsole"],
    }

    shoe_url = "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80"
    similar_items = find_similar_catalog_products(
        image=shoe_url,
        identified_info=shoe_info,
        top_k=3,
    )

    print(f"  Similar catalog recommendations returned: {len(similar_items)}")
    for item in similar_items:
        print(f"    - [{item.get('id')}] {item.get('brand')} {item.get('name')} ({item.get('category')}) - Score: {item.get('similarity_score')}")

    # Assert that results are returned and all belong strictly to the 'Shoes' category
    assert len(similar_items) > 0, "Expected shoe recommendations for in-catalog footwear category!"
    for item in similar_items:
        assert item.get("category") == "Shoes", f"Expected 'Shoes' category, got '{item.get('category')}' for {item.get('name')}"
    print("  >>> PASSED: Genuinely relevant catalog shoes returned, strictly isolated from other categories!")


if __name__ == "__main__":
    test_sony_headphone_photo()
    test_catalog_sample_image()
    test_sony_followup_buying_link()
    test_non_catalog_category_smartphone()
    test_in_catalog_category_shoe()
    print("\n" + "=" * 80)
    print("ALL OPEN-WORLD & CATEGORY RELEVANCE TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 80)


