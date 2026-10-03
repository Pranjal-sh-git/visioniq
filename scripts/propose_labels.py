"""scripts/propose_labels.py - Propose gold labels for RAG evaluation questions using LLM.

Rules:
1. For spec/procedural/out_of_docs rows:
   - Load ONLY that product's products.json entry and ALL of its chunks from data/corpus/chunks.jsonl.
   - Never query Azure Search, never use embeddings or any retrieval results.
   - Ask gpt-5-mini to return strict JSON:
     {"answerable": bool, "gold_chunk_ids": [...], "gold_keywords": [...], "reason": "..."}
   - Minimal set of chunks (max 3) directly stating the answer.
   - answerable=false if answer is not stated in JSON or chunks.
   - False-premise questions: gold chunk is the one stating the real fact.
   - gold_keywords only for spec rows, must be verbatim substring of products.json entry.
2. Apply results:
   - answerable=true & qtype in (spec, procedural): write gold_chunk_ids, gold_keywords (for spec).
   - answerable=false & qtype in (spec, procedural): relabel to out_of_docs, append 'RELABELED' to notes.
   - answerable=true & qtype == out_of_docs: do NOT change row, append 'CHECK-OOD' to notes.
   - spec row with no verbatim keyword: append 'CHECK-KW' to notes.
3. For unknown_product rows:
   - Script check (no LLM): verify question contains none of the 25 product names or brands; otherwise append 'CHECK-NAME'.
4. Cache LLM outputs in data/eval/label_proposals.json and log total tokens.
5. Generate human review sheet in data/eval/label_review.md.
"""

import argparse
import csv
import json
import logging
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Set

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure workspace root and backend are on sys.path
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
for directory in (str(ROOT_DIR), str(ROOT_DIR / "backend")):
    if directory not in sys.path:
        sys.path.insert(0, directory)

from backend.config import settings
from services.llm import get_azure_openai_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("visioniq.propose_labels")

CSV_PATH = ROOT_DIR / "data" / "eval" / "rag_eval.csv"
PRODUCTS_PATH = ROOT_DIR / "data" / "products" / "products.json"
CHUNKS_PATH = ROOT_DIR / "data" / "corpus" / "chunks.jsonl"
CACHE_PATH = ROOT_DIR / "data" / "eval" / "label_proposals.json"
REVIEW_MD_PATH = ROOT_DIR / "data" / "eval" / "label_review.md"

FLAG_TAGS = {"RELABELED", "CHECK-OOD", "CHECK-KW", "CHECK-NAME", "VERIFY"}

BASE_EVAL_ROWS = [
    {"id": "Q01", "split": "dev", "question": "What is the maximum battery life on a single charge?", "product_id": "P001", "qtype": "spec", "notes": ""},
    {"id": "Q02", "split": "test", "question": "Do these headphones support active noise cancellation (ANC)?", "product_id": "P003", "qtype": "spec", "notes": ""},
    {"id": "Q03", "split": "dev", "question": "Is the charging cable Type-C or Micro-USB?", "product_id": "P005", "qtype": "spec", "notes": "VERIFY"},
    {"id": "Q04", "split": "dev", "question": "What is the maximum weight capacity of this chair?", "product_id": "P007", "qtype": "spec", "notes": ""},
    {"id": "Q05", "split": "test", "question": "Are the armrests adjustable in 4D or just height?", "product_id": "P012", "qtype": "spec", "notes": ""},
    {"id": "Q06", "split": "dev", "question": "What material is the seat made of?", "product_id": "P010", "qtype": "spec", "notes": ""},
    {"id": "Q07", "split": "dev", "question": "Are these shoes waterproof or just water-resistant?", "product_id": "P015", "qtype": "spec", "notes": "VERIFY"},
    {"id": "Q08", "split": "test", "question": "What is the heel drop of these shoes in millimeters?", "product_id": "P017", "qtype": "spec", "notes": "VERIFY"},
    {"id": "Q09", "split": "dev", "question": "Do these shoes have a carbon fiber plate in the sole?", "product_id": "P019", "qtype": "spec", "notes": "VERIFY"},
    {"id": "Q10", "split": "dev", "question": "Does the smartwatch have built-in GPS or does it use connected GPS?", "product_id": "P021", "qtype": "spec", "notes": ""},
    {"id": "Q11", "split": "test", "question": "What is the screen size and resolution of this watch?", "product_id": "P023", "qtype": "spec", "notes": ""},
    {"id": "Q12", "split": "test", "question": "Is the watch glass made of sapphire?", "product_id": "P025", "qtype": "spec", "notes": "VERIFY"},
    {"id": "Q13", "split": "dev", "question": "How do I reset these headphones to factory settings?", "product_id": "P002", "qtype": "procedural", "notes": ""},
    {"id": "Q14", "split": "test", "question": "Headphones phone se connect nahi ho rahe pair kaise karu?", "product_id": "P004", "qtype": "procedural", "notes": "hinglish"},
    {"id": "Q15", "split": "dev", "question": "How do I replace the ear cushions when they tear?", "product_id": "P006", "qtype": "procedural", "notes": ""},
    {"id": "Q16", "split": "dev", "question": "The tilt mechanism is stuck how do I unlock it?", "product_id": "P008", "qtype": "procedural", "notes": ""},
    {"id": "Q17", "split": "test", "question": "What is the correct way to assemble the wheelbase?", "product_id": "P011", "qtype": "procedural", "notes": ""},
    {"id": "Q18", "split": "dev", "question": "Chair height adjust nahi ho rahi cylinder kaise theek karu?", "product_id": "P012", "qtype": "procedural", "notes": "hinglish"},
    {"id": "Q19", "split": "dev", "question": "Can I wash these shoes in the washing machine?", "product_id": "P014", "qtype": "procedural", "notes": ""},
    {"id": "Q20", "split": "test", "question": "How should I clean the suede material without ruining it?", "product_id": "P016", "qtype": "procedural", "notes": ""},
    {"id": "Q21", "split": "dev", "question": "Flat feet ke liye laces baandhne ka koi specific technique hai?", "product_id": "P018", "qtype": "procedural", "notes": "hinglish VERIFY"},
    {"id": "Q22", "split": "test", "question": "How do I change the time format from 12-hour to 24-hour?", "product_id": "P020", "qtype": "procedural", "notes": ""},
    {"id": "Q23", "split": "dev", "question": "Smartwatch ka strap kaise detach karte hain?", "product_id": "P020", "qtype": "procedural", "notes": "hinglish"},
    {"id": "Q24", "split": "test", "question": "My screen is stuck on the logo how do I restart the watch?", "product_id": "P023", "qtype": "procedural", "notes": ""},
    {"id": "Q25", "split": "dev", "question": "Will using these headphones for 10 hours a day cause hearing loss?", "product_id": "P001", "qtype": "out_of_docs", "notes": ""},
    {"id": "Q26", "split": "test", "question": "Can I use these headphones as a mic for recording ASMR videos?", "product_id": "P004", "qtype": "out_of_docs", "notes": ""},
    {"id": "Q27", "split": "dev", "question": "Is this ergonomic chair guaranteed to fix my lower back pain?", "product_id": "P009", "qtype": "out_of_docs", "notes": ""},
    {"id": "Q28", "split": "dev", "question": "Meri height 6 foot 5 hai kya ye chair mere liye comfortable rahegi?", "product_id": "P007", "qtype": "out_of_docs", "notes": "hinglish"},
    {"id": "Q29", "split": "test", "question": "Will these running shoes help me reduce my 5K race time?", "product_id": "P015", "qtype": "out_of_docs", "notes": ""},
    {"id": "Q30", "split": "dev", "question": "Can I wear these trail running shoes to a formal office party?", "product_id": "P019", "qtype": "out_of_docs", "notes": ""},
    {"id": "Q31", "split": "test", "question": "Does the heart rate sensor accurately detect incoming heart attacks?", "product_id": "P021", "qtype": "out_of_docs", "notes": ""},
    {"id": "Q32", "split": "dev", "question": "Kya main is smartwatch par PUBG jaise heavy games khel sakta hu?", "product_id": "P023", "qtype": "out_of_docs", "notes": "hinglish"},
    {"id": "Q33", "split": "dev", "question": "Can I connect my PlayStation 5 to this projector?", "product_id": "", "qtype": "unknown_product", "notes": ""},
    {"id": "Q34", "split": "test", "question": "Is the Sony FX3 camera good for low light shooting?", "product_id": "", "qtype": "unknown_product", "notes": ""},
    {"id": "Q35", "split": "dev", "question": "Does the Sony WH-1000XM4 support multipoint Bluetooth?", "product_id": "", "qtype": "unknown_product", "notes": "near-neighbor"},
    {"id": "Q36", "split": "dev", "question": "How long is the warranty on the Bose QuietComfort 45?", "product_id": "", "qtype": "unknown_product", "notes": "near-neighbor"},
    {"id": "Q37", "split": "test", "question": "Mere purane HP laptop ki battery kahan aur kitne ki milegi?", "product_id": "", "qtype": "unknown_product", "notes": "hinglish"},
    {"id": "Q38", "split": "dev", "question": "What is the exact thread count on these Egyptian cotton bedsheets?", "product_id": "", "qtype": "unknown_product", "notes": ""},
    {"id": "Q39", "split": "test", "question": "Can I safely use this hair straightener on wet hair?", "product_id": "", "qtype": "unknown_product", "notes": ""},
    {"id": "Q40", "split": "dev", "question": "How do I adjust the lumbar support on the Herman Miller Embody?", "product_id": "", "qtype": "unknown_product", "notes": "near-neighbor"},
]


def append_flag(existing_notes: str, flag: str) -> str:
    """Appends a flag to notes if not already present."""
    tokens = existing_notes.split() if existing_notes else []
    if flag not in tokens:
        tokens.append(flag)
    return " ".join(tokens)


def load_products_data() -> Dict[str, Dict[str, Any]]:
    with open(PRODUCTS_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)
    return {p["id"]: p for p in items if "id" in p}


def load_chunks_by_product() -> Dict[str, List[Dict[str, Any]]]:
    chunks_by_pid: Dict[str, List[Dict[str, Any]]] = {}
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            c = json.loads(line)
            pid = c.get("product_id")
            if pid:
                chunks_by_pid.setdefault(pid, []).append(c)
    return chunks_by_pid


def load_all_chunks_map() -> Dict[str, Dict[str, Any]]:
    chunks_map: Dict[str, Dict[str, Any]] = {}
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            c = json.loads(line)
            cid = c.get("chunk_id")
            if cid:
                chunks_map[cid] = c
    return chunks_map


def build_product_context(product: Dict[str, Any], chunks: List[Dict[str, Any]]) -> str:
    """Formats full product details and all chunks for prompt context."""
    prod_info = {
        "id": product.get("id"),
        "name": product.get("name"),
        "brand": product.get("brand"),
        "category": product.get("category"),
        "description": product.get("description"),
        "specifications": product.get("specifications", {}),
        "features": product.get("features", []),
    }
    prod_json_str = json.dumps(prod_info, indent=2, ensure_ascii=False)

    chunks_str_list = []
    for c in chunks:
        cid = c.get("chunk_id")
        sec = c.get("section")
        title = c.get("title")
        content = c.get("content", "")
        chunks_str_list.append(f"--- CHUNK ID: {cid} | Section: {sec} | Title: {title} ---\n{content}\n")

    all_chunks_text = "\n".join(chunks_str_list)

    return f"=== PRODUCTS.JSON CATALOG ENTRY ===\n{prod_json_str}\n\n=== CORPUS CHUNKS ({len(chunks)} chunks) ===\n{all_chunks_text}"


def call_llm_for_label(
    client,
    deployment: str,
    product: Dict[str, Any],
    chunks: List[Dict[str, Any]],
    question: str,
    qtype: str,
) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """Calls gpt-5-mini to propose gold chunk IDs and keywords."""
    context = build_product_context(product, chunks)

    system_prompt = (
        "You are VisionIQ's Expert Ground Truth Annotation Assistant for product Q&A.\n"
        "Your task is to analyze a user question against the given product's catalog entry and document chunks, "
        "and determine if the question is directly answerable, which minimal chunk(s) contain the answer, "
        "and verbatim keywords from the catalog entry.\n\n"
        "STRICT GROUNDING RULES:\n"
        "1. answerable: Set to true ONLY if the question's answer is DIRECTLY and explicitly stated in the catalog JSON or document chunks. "
        "Do NOT infer, speculate, extrapolate, or use general world knowledge. If the documents do not state the exact answer, answerable MUST be false.\n"
        "2. gold_chunk_ids: If answerable=true, select the MINIMAL set of chunk IDs (maximum 3, ideally 1-2) that directly provide the factual answer. "
        "Chunk IDs must match the chunk IDs in the provided corpus. If answerable=false, this MUST be an empty list [].\n"
        "3. False-premise questions: If the question assumes a false premise (e.g., 'Do these shoes have a carbon plate?'), and the chunks state the actual facts "
        "(or explicitly state it lacks that feature), set answerable=true and select the chunk that states the real fact. If the documents make no mention at all of the topic, answerable=false.\n"
        "4. gold_keywords: If the question type is 'spec' and answerable=true, list 1-3 short keyword phrases that appear VERBATIM (exact substring, case-insensitive) "
        "in the provided PRODUCTS.JSON CATALOG ENTRY (e.g. spec values like '30 hours' or 'Bluetooth 5.2'). If procedural or out_of_docs, leave this as [].\n"
        "5. Output format: You MUST reply with a single valid JSON object with NO surrounding markdown backticks, containing keys:\n"
        '   {"answerable": boolean, "gold_chunk_ids": [string], "gold_keywords": [string], "reason": string}'
    )

    user_prompt = (
        f"Product ID: {product.get('id')} ({product.get('name')})\n"
        f"Question Type: {qtype}\n"
        f"User Question: \"{question}\"\n\n"
        f"{context}"
    )

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_completion_tokens=2500,
        response_format={"type": "json_object"},
    )

    usage = response.usage
    tokens = {
        "prompt": usage.prompt_tokens if usage else 0,
        "completion": usage.completion_tokens if usage else 0,
        "total": usage.total_tokens if usage else 0,
    }

    content = response.choices[0].message.content or "{}"
    try:
        data = json.loads(content)
    except Exception as e:
        logger.warning(f"Failed to parse LLM JSON: {e}. Raw content: {content}")
        data = {"answerable": False, "gold_chunk_ids": [], "gold_keywords": [], "reason": "Failed to parse JSON"}

    return data, tokens


def check_unknown_product_brand_mention(question: str, products: Dict[str, Dict[str, Any]]) -> bool:
    """Checks if an unknown_product question contains any of the 25 product names or brands."""
    q_lower = question.lower()

    for pid, p in products.items():
        brand = p.get("brand", "").strip().lower()
        if brand and len(brand) >= 3:
            # Word boundary check for brand
            pattern = rf"\b{re.escape(brand)}\b"
            if re.search(pattern, q_lower):
                return True

        name = p.get("name", "").strip().lower()
        if name:
            # Check full name
            if name in q_lower:
                return True
            # Check significant model tokens (e.g. WH-1000XM5, ErgoChair, XT-6, Watch 6)
            for part in name.split():
                part_clean = part.strip(",.-()").lower()
                if len(part_clean) >= 4 and part_clean not in {"wireless", "headphones", "shoes", "chair", "smartwatch", "running", "classic"}:
                    if re.search(rf"\b{re.escape(part_clean)}\b", q_lower):
                        return True

    return False


def main():
    parser = argparse.ArgumentParser(description="Propose gold labels using LLM and generate human review sheet.")
    parser.add_argument("--force", action="store_true", help="Force re-query LLM even if cached")
    args = parser.parse_args()

    products = load_products_data()
    chunks_by_pid = load_chunks_by_product()
    all_chunks = load_all_chunks_map()

    # Load cache if exists
    cache: Dict[str, Any] = {}
    if CACHE_PATH.exists() and not args.force:
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                cache = json.load(f)
            logger.info(f"Loaded {len(cache)} cached proposals from {CACHE_PATH}")
        except Exception as e:
            logger.warning(f"Could not load cache: {e}")

    # Read the 40 rows
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    logger.info(f"Loaded {len(rows)} rows from {CSV_PATH}")

    aoai_client = get_azure_openai_client()
    deployment = settings.AZURE_OPENAI_DEPLOYMENT_NAME or "gpt-5-mini"

    total_tokens = {"prompt": 0, "completion": 0, "total": 0}
    labeled_rows: List[Dict[str, Any]] = []

    print("=" * 80)
    print("PROPOSING GOLD LABELS WITH GPT-5-MINI (LOCAL DOCS ONLY, NO SEARCH RETRIEVAL)")
    print("=" * 80)

    for r in BASE_EVAL_ROWS:
        qid = r["id"].strip()
        split = r["split"].strip()
        question = r["question"].strip()
        pid = r["product_id"].strip()
        original_qtype = r["qtype"].strip()
        existing_notes = r.get("notes", "").strip()

        logger.info(f"Processing {qid} ({split} | {original_qtype} | pid={pid or 'NONE'}): \"{question}\"")

        # Case 1: unknown_product
        if original_qtype == "unknown_product":
            notes = existing_notes
            has_brand_mention = check_unknown_product_brand_mention(question, products)
            if has_brand_mention:
                notes = append_flag(notes, "CHECK-NAME")

            labeled_rows.append({
                "id": qid,
                "split": split,
                "question": question,
                "product_id": "",
                "qtype": "unknown_product",
                "original_qtype": original_qtype,
                "gold_chunk_ids": "",
                "gold_keywords": "",
                "notes": notes,
                "llm_proposal": {
                    "answerable": False,
                    "gold_chunk_ids": [],
                    "gold_keywords": [],
                    "reason": "Unknown product question evaluated without catalog docs.",
                },
            })
            continue

        # Case 2: spec, procedural, out_of_docs
        product = products.get(pid)
        if not product:
            logger.error(f"Product {pid} not found for {qid}")
            sys.exit(1)

        product_chunks = chunks_by_pid.get(pid, [])
        valid_chunk_ids = {c["chunk_id"] for c in product_chunks}

        # Check cache (only use if answerable key exists and is not None)
        cached_proposal = cache.get(qid, {}).get("proposal", {})
        if qid in cache and not args.force and cached_proposal.get("answerable") is not None:
            proposal = cached_proposal
            tok = cache[qid].get("tokens", {"prompt": 0, "completion": 0, "total": 0})
            total_tokens["prompt"] += tok.get("prompt", 0)
            total_tokens["completion"] += tok.get("completion", 0)
            total_tokens["total"] += tok.get("total", 0)
            print(f"[{qid}] Loaded from cache (Answerable={proposal.get('answerable')})")
        else:
            proposal, tok = call_llm_for_label(
                client=aoai_client,
                deployment=deployment,
                product=product,
                chunks=product_chunks,
                question=question,
                qtype=original_qtype,
            )
            cache[qid] = {"proposal": proposal, "tokens": tok}
            total_tokens["prompt"] += tok["prompt"]
            total_tokens["completion"] += tok["completion"]
            total_tokens["total"] += tok["total"]
            print(f"[{qid}] LLM proposed: Answerable={proposal.get('answerable')} (Tokens: {tok['total']})")

        # Apply labeling rules
        answerable = bool(proposal.get("answerable"))
        raw_cids = proposal.get("gold_chunk_ids", [])
        raw_kws = proposal.get("gold_keywords", [])
        reason = proposal.get("reason", "")

        # Sanitize chunk IDs (must belong to this product's chunks)
        gold_cids = [cid for cid in raw_cids if cid in valid_chunk_ids][:3]

        # Sanitize keywords (must be verbatim substring of product catalog JSON entry)
        catalog_text = (
            f"{product.get('name', '')} {product.get('brand', '')} {product.get('description', '')} "
            + " ".join(product.get("features", [])) + " "
            + " ".join(f"{k} {v}" for k, v in product.get("specifications", {}).items())
        ).lower()

        valid_kws = []
        for kw in raw_kws:
            kw_clean = kw.strip()
            if kw_clean and kw_clean.lower() in catalog_text:
                valid_kws.append(kw_clean)

        current_qtype = original_qtype
        notes = existing_notes
        final_gold_chunk_ids = ""
        final_gold_keywords = ""

        if answerable and original_qtype in ("spec", "procedural"):
            final_gold_chunk_ids = "|".join(gold_cids)
            if original_qtype == "spec":
                if not valid_kws:
                    notes = append_flag(notes, "CHECK-KW")
                    # Fallback to model keywords if any, or leave empty
                    final_gold_keywords = "|".join(raw_kws) if raw_kws else ""
                else:
                    final_gold_keywords = "|".join(valid_kws)

        elif not answerable and original_qtype in ("spec", "procedural"):
            current_qtype = "out_of_docs"
            notes = append_flag(notes, "RELABELED")
            final_gold_chunk_ids = ""
            final_gold_keywords = ""

        elif answerable and original_qtype == "out_of_docs":
            # Do NOT change row, append CHECK-OOD
            notes = append_flag(notes, "CHECK-OOD")
            final_gold_chunk_ids = ""
            final_gold_keywords = ""

        elif not answerable and original_qtype == "out_of_docs":
            final_gold_chunk_ids = ""
            final_gold_keywords = ""

        labeled_rows.append({
            "id": qid,
            "split": split,
            "question": question,
            "product_id": pid,
            "qtype": current_qtype,
            "original_qtype": original_qtype,
            "gold_chunk_ids": final_gold_chunk_ids,
            "gold_keywords": final_gold_keywords,
            "notes": notes,
            "llm_proposal": proposal,
        })

    # Save cache
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved cache to {CACHE_PATH} (Total Tokens Used: {total_tokens['total']})")

    # Save updated CSV
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "split", "question", "product_id", "qtype", "gold_chunk_ids", "gold_keywords", "notes"],
        )
        writer.writeheader()
        for r in labeled_rows:
            writer.writerow({
                "id": r["id"],
                "split": r["split"],
                "question": r["question"],
                "product_id": r["product_id"],
                "qtype": r["qtype"],
                "gold_chunk_ids": r["gold_chunk_ids"],
                "gold_keywords": r["gold_keywords"],
                "notes": r["notes"],
            })
    logger.info(f"Updated evaluation CSV successfully written to {CSV_PATH}")

    # Build review markdown sheet
    build_review_sheet(labeled_rows, products, all_chunks, total_tokens)


def build_review_sheet(
    rows: List[Dict[str, Any]],
    products: Dict[str, Dict[str, Any]],
    all_chunks: Dict[str, Dict[str, Any]],
    total_tokens: Dict[str, int],
) -> None:
    lines = []
    lines.append("# VisionIQ RAG Evaluation — Label Review Sheet\n")
    lines.append("> **Labels are LLM-proposed from full product docs (no retrieval used) and must be human-reviewed.**\n")
    lines.append(f"- **Total Rows**: {len(rows)}")
    lines.append(f"- **Total LLM Tokens Used**: {total_tokens['total']:,} (Prompt: {total_tokens['prompt']:,}, Completion: {total_tokens['completion']:,})\n")

    # Identify flagged rows
    flagged_rows = []
    for r in rows:
        notes_tokens = set(r["notes"].split())
        matched_flags = notes_tokens.intersection(FLAG_TAGS)
        if matched_flags:
            flagged_rows.append((r, matched_flags))

    lines.append("## 1. Flagged Rows Requiring Immediate Review\n")
    if not flagged_rows:
        lines.append("None! All rows passed without flags.\n")
    else:
        lines.append(f"The following **{len(flagged_rows)} rows** contain flags (`RELABELED`, `CHECK-OOD`, `CHECK-KW`, `CHECK-NAME`, `VERIFY`):\n")
        lines.append("| ID | Split | QType | Question | Flags / Notes | Reason Summary |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for r, flags in flagged_rows:
            reason = r["llm_proposal"].get("reason", "").replace("\n", " ")
            lines.append(f"| **{r['id']}** | `{r['split']}` | `{r['qtype']}` | {r['question']} | `{r['notes']}` | {reason} |")
        lines.append("\n---\n")

    lines.append("## 2. Complete Evaluation Dataset Review (All 40 Rows)\n")

    for idx, r in enumerate(rows, 1):
        qid = r["id"]
        split = r["split"]
        qtype = r["qtype"]
        orig_qtype = r["original_qtype"]
        qtype_str = f"`{qtype}` (RELABELED from `{orig_qtype}`)" if qtype != orig_qtype else f"`{qtype}`"
        pid = r["product_id"]
        prod_name = products[pid]["name"] if pid in products else "N/A (Unknown Product)"
        notes = r["notes"] or "None"
        reason = r["llm_proposal"].get("reason", "No reason provided.")

        cids = [cid.strip() for cid in r["gold_chunk_ids"].split("|") if cid.strip()]
        kws = r["gold_keywords"] or "None"

        lines.append(f"### [{qid}] {r['question']}")
        lines.append(f"- **Split**: `{split}`")
        lines.append(f"- **Question Type**: {qtype_str}")
        lines.append(f"- **Product**: {pid} ({prod_name})")
        lines.append(f"- **Flags / Notes**: `{notes}`")
        lines.append(f"- **Model Reason**: *{reason}*")
        lines.append(f"- **Gold Keywords**: `{kws}`")
        lines.append(f"- **Gold Chunk IDs**: `{', '.join(cids) if cids else 'None'}`")

        if cids:
            lines.append("\n**Proposed Chunk Snippets (first 300 chars):**")
            for cid in cids:
                chunk = all_chunks.get(cid)
                if chunk:
                    snippet = chunk.get("content", "").replace("\n", " ").strip()[:300]
                    lines.append(f"  * **`{cid}`** ({chunk.get('section')} - {chunk.get('title')}): \"{snippet}...\"")
                else:
                    lines.append(f"  * **`{cid}`**: [Chunk content missing from chunks.jsonl]")
        lines.append("\n---\n")

    with open(REVIEW_MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(f"Human review sheet successfully written to {REVIEW_MD_PATH}")
    print("\n" + "=" * 80)
    print(f"Review sheet saved to: {REVIEW_MD_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    main()
