"""scripts/validate_eval_csv.py - Validate RAG evaluation CSV dataset.

Usage:
    python scripts/validate_eval_csv.py [--csv data/eval/rag_eval.csv]

Validates:
1. Required header: id,split,question,product_id,qtype,gold_chunk_ids,gold_keywords,notes
2. split must be 'dev' or 'test'.
3. qtype must be 'spec', 'procedural', 'out_of_docs', or 'unknown_product'.
4. product_id must exist in products.json for spec/procedural/out_of_docs, and be blank for unknown_product.
5. gold_chunk_ids:
   - Required for spec and procedural (pipe-separated).
   - Must be empty for out_of_docs and unknown_product.
   - Every chunk ID must exist in data/corpus/chunks.jsonl and match the row's product_id.
6. gold_keywords: required only for spec; optional/empty for others.
7. No duplicate questions.
8. Prints summary counts per (split x qtype) and lists all errors.
"""

import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import sys
from typing import Dict, List, Set

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
DEFAULT_CSV = ROOT_DIR / "data" / "eval" / "rag_eval.csv"
PRODUCTS_PATH = ROOT_DIR / "data" / "products" / "products.json"
CHUNKS_PATH = ROOT_DIR / "data" / "corpus" / "chunks.jsonl"

VALID_SPLITS = {"dev", "test"}
VALID_QTYPES = {"spec", "procedural", "out_of_docs", "unknown_product"}
REQUIRED_HEADER = [
    "id",
    "split",
    "question",
    "product_id",
    "qtype",
    "gold_chunk_ids",
    "gold_keywords",
    "notes",
]


def load_products_map(products_path: Path) -> Set[str]:
    if not products_path.exists():
        print(f"ERROR: products.json not found at {products_path}")
        sys.exit(1)
    with open(products_path, "r", encoding="utf-8") as f:
        products = json.load(f)
    return {p["id"] for p in products if "id" in p}


def load_chunks_map(chunks_path: Path) -> Dict[str, str]:
    """Loads chunks.jsonl returning a mapping of chunk_id -> product_id."""
    if not chunks_path.exists():
        print(f"ERROR: chunks.jsonl not found at {chunks_path}")
        sys.exit(1)
    chunk_to_product = {}
    with open(chunks_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            data = json.loads(line)
            cid = data.get("chunk_id")
            pid = data.get("product_id")
            if cid:
                chunk_to_product[cid] = pid
    return chunk_to_product


def validate_csv(csv_path: Path) -> bool:
    if not csv_path.exists():
        print(f"ERROR: CSV file not found: {csv_path}")
        return False

    valid_product_ids = load_products_map(PRODUCTS_PATH)
    chunk_to_product = load_chunks_map(CHUNKS_PATH)

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            print("ERROR: CSV file is empty.")
            return False

    # Check header
    clean_header = [col.strip() for col in header]
    if clean_header != REQUIRED_HEADER:
        print(f"ERROR: Invalid header.\n  Expected: {','.join(REQUIRED_HEADER)}\n  Found:    {','.join(clean_header)}")
        return False

    with open(csv_path, "r", encoding="utf-8") as f:
        dict_reader = csv.DictReader(f)
        rows = list(dict_reader)

    print("=" * 80)
    print(f"VALIDATING EVALUATION CSV: {csv_path.name} (Total Rows: {len(rows)})")
    print("=" * 80)

    errors: List[str] = []
    seen_questions: Dict[str, int] = {}
    split_qtype_counts = Counter()

    for row_idx, r in enumerate(rows, start=2):  # 1-indexed, line 2 is first data row
        qid = r.get("id", "").strip()
        split = r.get("split", "").strip().lower()
        question = r.get("question", "").strip()
        pid = r.get("product_id", "").strip()
        qtype = r.get("qtype", "").strip().lower()
        gold_chunk_ids_raw = r.get("gold_chunk_ids", "").strip()
        gold_keywords_raw = r.get("gold_keywords", "").strip()

        row_prefix = f"Row {row_idx} [id={qid or 'MISSING'}]:"

        # 1. ID check
        if not qid:
            errors.append(f"{row_prefix} 'id' field is missing or empty.")

        # 2. Split check
        if split not in VALID_SPLITS:
            errors.append(f"{row_prefix} Invalid split '{split}'. Must be one of {sorted(VALID_SPLITS)}.")

        # 3. Qtype check
        if qtype not in VALID_QTYPES:
            errors.append(f"{row_prefix} Invalid qtype '{qtype}'. Must be one of {sorted(VALID_QTYPES)}.")

        # Track count
        split_qtype_counts[(split, qtype)] += 1

        # 4. Question check & duplicate detection
        if not question:
            errors.append(f"{row_prefix} 'question' is empty.")
        else:
            q_norm = question.lower()
            if q_norm in seen_questions:
                errors.append(f"{row_prefix} Duplicate question (first seen in row {seen_questions[q_norm]}): \"{question}\"")
            else:
                seen_questions[q_norm] = row_idx

        # 5. Product ID rules
        if qtype == "unknown_product":
            if pid:
                errors.append(f"{row_prefix} product_id must be blank for 'unknown_product', found '{pid}'.")
        else:
            if not pid:
                errors.append(f"{row_prefix} product_id is required for '{qtype}'.")
            elif pid not in valid_product_ids:
                errors.append(f"{row_prefix} product_id '{pid}' does not exist in products.json.")

        # 6. Gold chunk IDs rules
        chunk_ids = [c.strip() for c in gold_chunk_ids_raw.split("|") if c.strip()]
        if qtype in {"spec", "procedural"}:
            if not chunk_ids:
                errors.append(f"{row_prefix} gold_chunk_ids is required for '{qtype}'.")
            else:
                for cid in chunk_ids:
                    if cid not in chunk_to_product:
                        errors.append(f"{row_prefix} gold_chunk_id '{cid}' not found in chunks.jsonl.")
                    else:
                        chunk_pid = chunk_to_product[cid]
                        if chunk_pid != pid:
                            errors.append(f"{row_prefix} gold_chunk_id '{cid}' belongs to product '{chunk_pid}', not row product_id '{pid}'.")
        elif qtype in {"out_of_docs", "unknown_product"}:
            if chunk_ids:
                errors.append(f"{row_prefix} gold_chunk_ids must be empty for '{qtype}', found '{gold_chunk_ids_raw}'.")

        # 7. Gold keywords rules
        keywords = [k.strip() for k in gold_keywords_raw.split("|") if k.strip()]
        if qtype == "spec":
            if not keywords:
                errors.append(f"{row_prefix} gold_keywords is required for 'spec' (used for JSON baseline).")

    # Summary table
    print("\nCounts per (split x qtype):")
    print(f"{'Split':<10} | {'Question Type':<20} | {'Count':<8}")
    print("-" * 45)
    for sp in sorted(VALID_SPLITS):
        for qt in sorted(VALID_QTYPES):
            cnt = split_qtype_counts.get((sp, qt), 0)
            if cnt > 0:
                print(f"{sp:<10} | {qt:<20} | {cnt:<8}")

    print("\n" + "=" * 80)
    if errors:
        print(f"VALIDATION FAILED WITH {len(errors)} ERROR(S):")
        for err in errors:
            print(f"  [X] {err}")
        print("=" * 80)
        return False
    else:
        print(f"VALIDATION PASSED: 0 errors detected across {len(rows)} row(s).")
        print("=" * 80)
        return True


def main():
    parser = argparse.ArgumentParser(description="Validate evaluation dataset CSV format and integrity.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Path to evaluation CSV file")
    args = parser.parse_args()

    success = validate_csv(args.csv)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
