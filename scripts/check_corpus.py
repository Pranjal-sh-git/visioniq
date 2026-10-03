"""Corpus Consistency Checker for VisionIQ RAG.

Scans all generated markdown documents in data/corpus/<product_id>/*.md and checks:
1. Every numeric value or specification against authentic entries in data/products/products.json.
2. Alphanumeric spec tokens (IP67, 5ATM, Bluetooth 5.2, aptX, LDAC, USB-C, MIL-STD, etc.) not in products.json.

Writes a comprehensive consistency report to data/corpus/consistency_report.md.
Follows rule: Do not auto-fix; just list.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import re
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("visioniq.check_corpus")

SPEC_TOKEN_REGEX = re.compile(
    r"\b("
    r"IP\d{2}[A-Za-z]?"
    r"|\d+ATM"
    r"|Bluetooth\s*\d+(?:\.\d+)?"
    r"|aptX(?:-Adaptive|-HD|-LL)?"
    r"|LDAC"
    r"|AAC"
    r"|SBC"
    r"|LC3"
    r"|USB-C"
    r"|Type-C"
    r"|MIL-STD(?:-[A-Za-z0-9]+)?"
    r"|NFC"
    r"|Qi"
    r"|AMOLED"
    r"|OLED"
    r"|BIA"
    r"|ECG"
    r"|SpO2"
    r"|GPS"
    r"|GLONASS"
    r"|Galileo"
    r")\b",
    re.IGNORECASE
)


def extract_numbers_and_specs_from_product(product: dict) -> dict:
    """Extracts all authentic numbers, spec units, and identifiers from a product JSON."""
    raw_texts = [
        product.get("name", ""),
        product.get("brand", ""),
        product.get("category", ""),
        product.get("description", ""),
    ]
    for k, v in product.get("specifications", {}).items():
        raw_texts.append(f"{k}: {v}")
    for feat in product.get("features", []):
        raw_texts.append(feat)

    combined_text = " ".join(raw_texts)

    # 1. All standalone numbers (integers and floats)
    numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", combined_text))

    # 2. Specs with units (e.g., 30 hours, 250g, 30mm, 5.2, 3.5mm, 40mm)
    spec_tokens = set(re.findall(
        r"\b\d+(?:\.\d+)?\s*(?:mm|cm|m|g|kg|lbs|oz|hours?|hrs?|h|mins?|minutes?|s|seconds?|dB|Hz|kHz|W|mAh|V|%|ms|k)\b",
        combined_text,
        re.IGNORECASE
    ))

    # 3. Model tokens like XM5, V1, 1000XM5, 990, 700
    alphanumeric_tokens = set(re.findall(r"\b[A-Za-z0-9\-_/]+\d+[A-Za-z0-9\-_/]*\b", combined_text))

    return {
        "text": combined_text,
        "text_lower": combined_text.lower(),
        "numbers": numbers,
        "specs": {s.lower().replace(" ", "") for s in spec_tokens},
        "raw_specs": spec_tokens,
        "alphanumeric": alphanumeric_tokens,
    }


def analyze_document(doc_path: Path, product_specs: dict) -> list[dict]:
    """Analyzes a generated markdown doc and flags unlisted numbers and spec tokens."""
    content = doc_path.read_text(encoding="utf-8")
    
    # Strip YAML front matter
    body = re.sub(r"^---[\s\S]*?---\n*", "", content)
    
    lines = body.splitlines()
    flagged = []

    procedural_patterns = [
        r"^(?:#{1,6}\s+)?(?:Q)?\d+[\.\)]\s+",  # Step / Section numbers: "1. ", "## 1. ", "Q1. "
        r"\b(?:1|2|3|5|7|10|15|30)\s*(?:seconds?|secs?|s)\b",  # button press timers
        r"\b(?:1|2|3|5|10|12|15)\s*(?:years?|yr)\b",  # warranty years
        r"\b(?:14|30|60|90)\s*days?\b",  # return policy: "30 days"
        r"\b(?:24/7|24\s*hours?)\b",  # support: "24/7 support"
        r"\b\d{4}\b",  # Years like 2024, 2025, 2026
    ]

    for line_idx, line in enumerate(lines, start=1):
        clean_line = line.strip()
        if not clean_line:
            continue

        # Skip note/disclaimer line
        if clean_line.startswith("Note: This is an illustrative sample document"):
            continue

        # 1. Alphanumeric Spec Token Check
        spec_matches = SPEC_TOKEN_REGEX.finditer(clean_line)
        for s_match in spec_matches:
            token = s_match.group(0).strip()
            token_clean = token.lower()
            if token_clean not in product_specs["text_lower"]:
                flagged.append({
                    "line_number": line_idx,
                    "value": token,
                    "context": clean_line,
                    "classification": "Unlisted spec tokens",
                })

        # 2. Numeric / Spec Check
        matches = re.finditer(
            r"\b\d+(?:\.\d+)?(?:\s*(?:mm|cm|m|g|kg|lbs|oz|hours?|hrs?|h|mins?|minutes?|s|seconds?|dB|Hz|kHz|W|mAh|V|%|ms|year|years|day|days))?\b",
            clean_line,
            re.IGNORECASE
        )

        for match in matches:
            matched_str = match.group(0).strip()
            num_match = re.search(r"\d+(?:\.\d+)?", matched_str)
            if not num_match:
                continue
            num_part = num_match.group(0)

            # Check if this exact number or spec is in products.json
            normalized_spec = matched_str.lower().replace(" ", "")
            is_matched = (
                num_part in product_specs["numbers"]
                or normalized_spec in product_specs["specs"]
                or matched_str in product_specs["text"]
            )

            if not is_matched:
                is_procedural = any(re.search(pat, clean_line, re.IGNORECASE) for pat in procedural_patterns)
                classification = "Generic Procedural/Policy" if is_procedural else "Unlisted Numeric Spec"
                
                flagged.append({
                    "line_number": line_idx,
                    "value": matched_str,
                    "context": clean_line,
                    "classification": classification,
                })

    return flagged


def generate_consistency_report():
    products_path = PROJECT_ROOT / "data" / "products" / "products.json"
    corpus_dir = PROJECT_ROOT / "data" / "corpus"
    report_path = corpus_dir / "consistency_report.md"

    with open(products_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    logger.info(f"Checking consistency for {len(products)} products in {corpus_dir}")

    total_docs = 0
    total_flagged_items = 0
    per_product_reports = {}
    classification_counts = {
        "Generic Procedural/Policy": 0,
        "Unlisted Numeric Spec": 0,
        "Unlisted spec tokens": 0,
    }

    for product in products:
        p_id = product["id"]
        prod_specs = extract_numbers_and_specs_from_product(product)
        prod_dir = corpus_dir / p_id
        
        per_product_reports[p_id] = {
            "name": product["name"],
            "category": product["category"],
            "docs": {},
        }

        if not prod_dir.exists():
            continue

        for doc_file in sorted(prod_dir.glob("*.md")):
            if doc_file.name == "consistency_report.md":
                continue
            total_docs += 1
            doc_flagged = analyze_document(doc_file, prod_specs)
            per_product_reports[p_id]["docs"][doc_file.name] = doc_flagged
            total_flagged_items += len(doc_flagged)
            for item in doc_flagged:
                cls = item["classification"]
                classification_counts[cls] = classification_counts.get(cls, 0) + 1

    # Format Markdown Report
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    report_lines = [
        "# VisionIQ RAG Corpus Specification Consistency Report",
        "",
        f"> **Generated at**: `{now_iso}`  ",
        f"> **Corpus Location**: `data/corpus/`  ",
        "> **Rule**: Flag every numeric value or spec not present in `data/products/products.json`. Do not auto-fix; list for audit.",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        "",
        f"| Metric | Count |",
        f"| :--- | :---: |",
        f"| **Total Products Audited** | {len(products)} |",
        f"| **Total Markdown Documents Checked** | {total_docs} |",
        f"| **Total Flagged Items** | {total_flagged_items} |",
        f"| **Plausible Procedural / Policy Numbers** (step #s, button timers, warranty durations) | {classification_counts.get('Generic Procedural/Policy', 0)} |",
        f"| **Unlisted Numeric Specifications** | {classification_counts.get('Unlisted Numeric Spec', 0)} |",
        f"| **Unlisted Spec Tokens** (alphanumeric protocols, certifications, standards) | {classification_counts.get('Unlisted spec tokens', 0)} |",
        "",
        "---",
        "",
        "## 2. Per-Product Audit Breakdown",
        "",
    ]

    for p_id, p_data in sorted(per_product_reports.items()):
        report_lines.append(f"### {p_id} — {p_data['name']} ({p_data['category']})")
        report_lines.append("")
        
        has_flags = False
        for doc_name, flagged_list in sorted(p_data["docs"].items()):
            if flagged_list:
                has_flags = True
                report_lines.append(f"#### `{doc_name}` ({len(flagged_list)} flagged items)")
                report_lines.append("| Line | Flagged Value | Classification | Context |")
                report_lines.append("| :---: | :--- | :--- | :--- |")
                for item in flagged_list[:20]:
                    safe_ctx = item["context"].replace("|", "\\|")
                    report_lines.append(f"| {item['line_number']} | `{item['value']}` | {item['classification']} | {safe_ctx} |")
                if len(flagged_list) > 20:
                    report_lines.append(f"| ... | *and {len(flagged_list) - 20} more* | ... | ... |")
                report_lines.append("")

        if not has_flags:
            report_lines.append("No unlisted numeric values or spec tokens detected. All specs strictly match `products.json`.")
            report_lines.append("")

    report_content = "\n".join(report_lines) + "\n"
    report_path.write_text(report_content, encoding="utf-8")
    logger.info(f"Report written to {report_path} ({len(report_lines)} lines)")

    print("\n" + "=" * 70)
    print("CONSISTENCY REPORT SUMMARY")
    print("=" * 70)
    print(f"Products checked: {len(products)}")
    print(f"Documents checked: {total_docs}")
    print(f"Total flagged items: {total_flagged_items}")
    print(f"  - Procedural / Policy: {classification_counts.get('Generic Procedural/Policy', 0)}")
    print(f"  - Unlisted Numeric Specs: {classification_counts.get('Unlisted Numeric Spec', 0)}")
    print(f"  - Unlisted Spec Tokens: {classification_counts.get('Unlisted spec tokens', 0)}")
    print(f"Report saved to: {report_path}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    generate_consistency_report()
