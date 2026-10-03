"""Chunk Corpus Script for VisionIQ RAG.

Iterates over all generated markdown documents in data/corpus/<product_id>/*.md,
chunks each document using services.rag.chunker.chunk_markdown,
saves the resulting chunks into data/corpus/chunks.jsonl,
and prints statistics:
  - total number of chunks
  - min / median / max tokens
  - chunks per section type
"""

from collections import Counter
import json
import logging
from pathlib import Path
import statistics
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.rag.chunker import chunk_markdown, count_tokens

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("visioniq.chunk_corpus")


def chunk_all_documents():
    products_path = PROJECT_ROOT / "data" / "products" / "products.json"
    corpus_dir = PROJECT_ROOT / "data" / "corpus"
    output_jsonl = corpus_dir / "chunks.jsonl"

    with open(products_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    product_map = {p["id"]: p for p in products}
    all_chunks = []
    section_counter = Counter()
    token_counts = []

    logger.info(f"Scanning documents in {corpus_dir}...")
    doc_paths = sorted(corpus_dir.glob("*/*.md"))

    for doc_path in doc_paths:
        if doc_path.name in ("consistency_report.md", "README.md"):
            continue

        product_id = doc_path.parent.name
        section = doc_path.stem  # e.g. user_manual, faq, warranty, usage_guide
        
        prod_meta = product_map.get(product_id, {})
        metadata = {
            "product_id": product_id,
            "product_name": prod_meta.get("name", product_id),
            "category": prod_meta.get("category", "General"),
            "section": section,
            "is_synthetic": True,
        }

        content = doc_path.read_text(encoding="utf-8")
        doc_chunks = chunk_markdown(content, metadata=metadata)

        for chunk in doc_chunks:
            all_chunks.append(chunk)
            section_counter[chunk["section"]] += 1
            token_counts.append(chunk["token_count"])

    # Write chunks.jsonl
    with open(output_jsonl, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    logger.info(f"Saved {len(all_chunks)} chunks to {output_jsonl}")

    # Compute Statistics
    min_tokens = min(token_counts) if token_counts else 0
    max_tokens = max(token_counts) if token_counts else 0
    median_tokens = statistics.median(token_counts) if token_counts else 0
    mean_tokens = statistics.mean(token_counts) if token_counts else 0

    print("\n" + "=" * 70)
    print("VISIONIQ RAG CORPUS CHUNKING STATISTICS")
    print("=" * 70)
    print(f"Total Markdown Documents Processed: {len(doc_paths)}")
    print(f"Total Chunks Generated:             {len(all_chunks)}")
    print(f"Token Size Distribution (cl100k_base):")
    print(f"  - Min Tokens:    {min_tokens}")
    print(f"  - Median Tokens: {median_tokens:.1f}")
    print(f"  - Mean Tokens:   {mean_tokens:.1f}")
    print(f"  - Max Tokens:    {max_tokens}")
    print("\nChunks Per Section Type:")
    for sec, count in sorted(section_counter.items()):
        print(f"  - {sec:15s}: {count:4d} chunks ({count / len(all_chunks) * 100:.1f}%)")
    print(f"\nArtifact Saved: {output_jsonl}")
    print("=" * 70 + "\n")

    return all_chunks


if __name__ == "__main__":
    chunk_all_documents()
