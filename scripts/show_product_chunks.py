"""scripts/show_product_chunks.py - Inspect product catalog entry and its corpus chunks.

Usage:
    python scripts/show_product_chunks.py <product_id>

Outputs:
1. Product metadata and specs from data/products/products.json.
2. Every chunk of that product from data/corpus/chunks.jsonl (chunk_id, section, title, content).

Local only, no Azure calls.
"""

import argparse
import json
from pathlib import Path
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
PRODUCTS_PATH = ROOT_DIR / "data" / "products" / "products.json"
CHUNKS_PATH = ROOT_DIR / "data" / "corpus" / "chunks.jsonl"


def show_product_chunks(product_id: str) -> None:
    product_id = product_id.strip()
    if not product_id:
        print("ERROR: product_id must not be empty.")
        sys.exit(1)

    if not PRODUCTS_PATH.exists():
        print(f"ERROR: Products file not found at {PRODUCTS_PATH}")
        sys.exit(1)

    if not CHUNKS_PATH.exists():
        print(f"ERROR: Chunks file not found at {CHUNKS_PATH}")
        sys.exit(1)

    with open(PRODUCTS_PATH, "r", encoding="utf-8") as f:
        products = json.load(f)

    target_product = next((p for p in products if p.get("id") == product_id), None)
    if not target_product:
        print(f"ERROR: Product '{product_id}' not found in {PRODUCTS_PATH}")
        available_ids = [p.get("id") for p in products if "id" in p]
        print(f"Available product IDs ({len(available_ids)}): {', '.join(available_ids)}")
        sys.exit(1)

    # 1. Print products.json entry
    print("=" * 80)
    print(f"PRODUCTS.JSON ENTRY FOR: {product_id} ({target_product.get('name', '')})")
    print("=" * 80)
    print(json.dumps(target_product, indent=2, ensure_ascii=False))

    # 2. Find and print every chunk of that product
    matching_chunks = []
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            chunk = json.loads(line)
            if chunk.get("product_id") == product_id:
                matching_chunks.append(chunk)

    print("\n" + "=" * 80)
    print(f"CORPUS CHUNKS FOR {product_id} (Total: {len(matching_chunks)} chunks)")
    print("=" * 80)

    if not matching_chunks:
        print(f"No chunks found in {CHUNKS_PATH} for product_id '{product_id}'.")
        return

    for idx, c in enumerate(matching_chunks, 1):
        print(f"\n[{idx}/{len(matching_chunks)}] Chunk ID: {c.get('chunk_id')}")
        print(f"  * Section    : {c.get('section')}")
        print(f"  * Title      : {c.get('title')}")
        print(f"  * Token Count: {c.get('token_count')}")
        print("  * Content    :")
        for line in c.get("content", "").splitlines():
            print(f"      {line}")
        print("-" * 80)


def main():
    parser = argparse.ArgumentParser(description="Show product catalog entry and all its corpus chunks.")
    parser.add_argument("product_id", help="Product ID (e.g., P001, P010, P019)")
    args = parser.parse_args()

    show_product_chunks(args.product_id)


if __name__ == "__main__":
    main()
