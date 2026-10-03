"""scripts/draft_questions.py - Generate 24 candidate eval questions, filter by 4-gram overlap,
label with strict labeler, select 8 spec + 8 procedural (4 dev + 4 test each), and append to rag_eval.csv.

Rules:
1. 24 candidate questions (12 spec, 12 procedural), 3 spec + 3 procedural per category.
2. Products chosen with fewest existing rows, no product used twice for the same qtype within a category.
3. Spec candidates: model sees ONLY products.json entry.
4. Procedural candidates: model sees that product's chunks.
5. 6 of 24 candidates in romanized Hinglish.
6. Reject candidate if it shares 4+ consecutive words (lowercased, punctuation stripped) with any chunk of its product.
7. Strict labeler keeps ONLY answerable=true candidates.
8. Select up to 8 spec + 8 procedural: 4 dev + 4 test per qtype, spread across categories.
9. Append as Q41-Q56 to data/eval/rag_eval.csv with notes containing "LLM-DRAFTED".
10. Add "LLM-drafted questions" section to data/eval/label_review.md.
"""

import argparse
import csv
import json
import logging
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
for directory in (str(ROOT_DIR), str(ROOT_DIR / "backend")):
    if directory not in sys.path:
        sys.path.insert(0, directory)

from backend.config import settings
from services.llm import get_azure_openai_client
from scripts.propose_labels import (
    load_products_data,
    load_chunks_by_product,
    load_all_chunks_map,
    call_llm_for_label,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("visioniq.draft_questions")

CSV_PATH = ROOT_DIR / "data" / "eval" / "rag_eval.csv"
PRODUCTS_PATH = ROOT_DIR / "data" / "products" / "products.json"
CHUNKS_PATH = ROOT_DIR / "data" / "corpus" / "chunks.jsonl"
REVIEW_MD_PATH = ROOT_DIR / "data" / "eval" / "label_review.md"
DRAFT_CACHE_PATH = ROOT_DIR / "data" / "eval" / "draft_candidates.json"

# 24 Candidate configurations (3 spec + 3 procedural per category, 6 Hinglish)
# Products selected based on fewest existing rows in rag_eval.csv
CANDIDATE_CONFIGS = [
    # --- Category: Headphones (P001-P006) ---
    {"candidate_id": "C01", "category": "headphones", "product_id": "P002", "qtype": "spec", "is_hinglish": False},
    {"candidate_id": "C02", "category": "headphones", "product_id": "P005", "qtype": "spec", "is_hinglish": True},
    {"candidate_id": "C03", "category": "headphones", "product_id": "P006", "qtype": "spec", "is_hinglish": False},
    {"candidate_id": "C04", "category": "headphones", "product_id": "P001", "qtype": "procedural", "is_hinglish": False},
    {"candidate_id": "C05", "category": "headphones", "product_id": "P003", "qtype": "procedural", "is_hinglish": True},
    {"candidate_id": "C06", "category": "headphones", "product_id": "P004", "qtype": "procedural", "is_hinglish": False},

    # --- Category: Chairs (P007-P013) ---
    {"candidate_id": "C07", "category": "chairs", "product_id": "P013", "qtype": "spec", "is_hinglish": True},
    {"candidate_id": "C08", "category": "chairs", "product_id": "P008", "qtype": "spec", "is_hinglish": False},
    {"candidate_id": "C09", "category": "chairs", "product_id": "P009", "qtype": "spec", "is_hinglish": False},
    {"candidate_id": "C10", "category": "chairs", "product_id": "P013", "qtype": "procedural", "is_hinglish": False},
    {"candidate_id": "C11", "category": "chairs", "product_id": "P010", "qtype": "procedural", "is_hinglish": True},
    {"candidate_id": "C12", "category": "chairs", "product_id": "P011", "qtype": "procedural", "is_hinglish": False},

    # --- Category: Shoes (P014-P019) ---
    {"candidate_id": "C13", "category": "shoes", "product_id": "P014", "qtype": "spec", "is_hinglish": False},
    {"candidate_id": "C14", "category": "shoes", "product_id": "P016", "qtype": "spec", "is_hinglish": False},
    {"candidate_id": "C15", "category": "shoes", "product_id": "P018", "qtype": "spec", "is_hinglish": False},
    {"candidate_id": "C16", "category": "shoes", "product_id": "P017", "qtype": "procedural", "is_hinglish": True},
    {"candidate_id": "C17", "category": "shoes", "product_id": "P015", "qtype": "procedural", "is_hinglish": False},
    {"candidate_id": "C18", "category": "shoes", "product_id": "P019", "qtype": "procedural", "is_hinglish": False},

    # --- Category: Watches (P020-P025) ---
    {"candidate_id": "C19", "category": "watches", "product_id": "P022", "qtype": "spec", "is_hinglish": False},
    {"candidate_id": "C20", "category": "watches", "product_id": "P024", "qtype": "spec", "is_hinglish": True},
    {"candidate_id": "C21", "category": "watches", "product_id": "P025", "qtype": "spec", "is_hinglish": False},
    {"candidate_id": "C22", "category": "watches", "product_id": "P024", "qtype": "procedural", "is_hinglish": False},
    {"candidate_id": "C23", "category": "watches", "product_id": "P021", "qtype": "procedural", "is_hinglish": False},
    {"candidate_id": "C24", "category": "watches", "product_id": "P020", "qtype": "procedural", "is_hinglish": False},
]


def extract_words(text: str) -> List[str]:
    """Lowercases text and strips punctuation to a list of tokens."""
    return re.findall(r"\b\w+\b", text.lower())


def check_ngram_overlap(question: str, chunks: List[Dict[str, Any]], n: int = 4) -> Optional[Tuple[str, str]]:
    """Checks if the question shares a run of n+ consecutive words with any chunk."""
    q_words = extract_words(question)
    if len(q_words) < n:
        return None
    q_ngrams = {tuple(q_words[i : i + n]) for i in range(len(q_words) - n + 1)}

    for c in chunks:
        c_words = extract_words(c.get("content", ""))
        for i in range(len(c_words) - n + 1):
            gram = tuple(c_words[i : i + n])
            if gram in q_ngrams:
                return " ".join(gram), c.get("chunk_id", "")
    return None


def draft_spec_question(
    client,
    deployment: str,
    product: Dict[str, Any],
    is_hinglish: bool,
) -> Tuple[str, Dict[str, int]]:
    """Drafts a casual customer question about a spec attribute from products.json ONLY."""
    prod_json = json.dumps(product, indent=2, ensure_ascii=False)

    lang_instr = (
        "Write the question in natural, everyday conversational Romanized Hinglish (Hindi written in Latin script, e.g. 'Is chair ka maximum load kitna hai?')."
        if is_hinglish
        else "Write the question in natural, casual conversational English as a typical shopper would ask."
    )

    system_prompt = (
        "You are an assistant creating realistic customer evaluation questions for an e-commerce catalog.\n"
        "You will be given ONLY a product's catalog JSON entry (not documentation chunks).\n"
        "Your task is to write ONE natural customer question inquiring about one specific specification or feature "
        "whose value is explicitly stated in the catalog entry.\n\n"
        "CRITICAL RULES:\n"
        "1. Casual customer phrasing: Do NOT copy or reuse the field-name wording (e.g. if field is 'battery_life', do not ask 'What is the battery life?'; ask 'How many hours will this last on a full charge?').\n"
        "2. Do NOT copy long phrases verbatim from the description or features.\n"
        "3. Ensure the question can be definitively answered by that specification value.\n"
        f"4. Language: {lang_instr}\n"
        "5. Output format: Return strict JSON: {\"question\": \"...\", \"attribute_asked\": \"...\"}\n"
    )

    user_prompt = f"Product Catalog Entry:\n{prod_json}"

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_completion_tokens=1500,
        response_format={"type": "json_object"},
    )

    usage = response.usage
    tokens = {
        "prompt": usage.prompt_tokens if usage else 0,
        "completion": usage.completion_tokens if usage else 0,
        "total": usage.total_tokens if usage else 0,
    }

    try:
        data = json.loads(response.choices[0].message.content or "{}")
        return data.get("question", "").strip(), tokens
    except Exception:
        return "", tokens


def draft_procedural_question(
    client,
    deployment: str,
    product: Dict[str, Any],
    chunks: List[Dict[str, Any]],
    is_hinglish: bool,
) -> Tuple[str, Dict[str, int]]:
    """Drafts a customer question about a procedure (setup, pairing, cleaning, assembly, troubleshooting) from chunks."""
    chunks_text = "\n\n".join(f"[{c['chunk_id']} | {c['title']}]:\n{c['content']}" for c in chunks)

    lang_instr = (
        "Write the question in natural, everyday conversational Romanized Hinglish (Hindi written in Latin script, e.g. 'Headphones ko saf karne ka sahi tarika kya hai?')."
        if is_hinglish
        else "Write the question in natural, everyday conversational English as a real customer."
    )

    system_prompt = (
        "You are an assistant creating realistic customer evaluation questions for product customer support.\n"
        "You will be given document chunks describing procedures (setup, pairing, cleaning, assembly, troubleshooting).\n"
        "Your task is to write ONE realistic question a real customer would ask about a procedure that IS directly answered "
        "by the provided chunks.\n\n"
        "CRITICAL RULES:\n"
        "1. Everyday words: Ask casually about a real situation (e.g. how to pair, how to clean, how to assemble a part, or fix a specific problem).\n"
        "2. Avoid verbatim phrasing: Do NOT copy 4 or more consecutive words from any of the chunks. Rephrase in everyday language.\n"
        "3. Grounded: The answer must be clearly contained within the provided procedural chunks.\n"
        f"4. Language: {lang_instr}\n"
        "5. Output format: Return strict JSON: {\"question\": \"...\", \"procedure_topic\": \"...\"}\n"
    )

    user_prompt = f"Product: {product.get('id')} - {product.get('name')}\n\n{chunks_text}"

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_completion_tokens=1500,
        response_format={"type": "json_object"},
    )

    usage = response.usage
    tokens = {
        "prompt": usage.prompt_tokens if usage else 0,
        "completion": usage.completion_tokens if usage else 0,
        "total": usage.total_tokens if usage else 0,
    }

    try:
        data = json.loads(response.choices[0].message.content or "{}")
        return data.get("question", "").strip(), tokens
    except Exception:
        return "", tokens


def main():
    parser = argparse.ArgumentParser(description="Draft new eval questions, filter, label, and append to rag_eval.csv")
    parser.add_argument("--force", action="store_true", help="Force regenerate questions instead of using draft cache")
    args = parser.parse_args()

    products = load_products_data()
    chunks_by_pid = load_chunks_by_product()
    all_chunks = load_all_chunks_map()

    aoai_client = get_azure_openai_client()
    deployment = settings.AZURE_OPENAI_DEPLOYMENT_NAME or "gpt-5-mini"

    draft_cache: Dict[str, Any] = {}
    if DRAFT_CACHE_PATH.exists() and not args.force:
        try:
            with open(DRAFT_CACHE_PATH, "r", encoding="utf-8") as f:
                draft_cache = json.load(f)
            logger.info(f"Loaded draft cache with {len(draft_cache)} items from {DRAFT_CACHE_PATH}")
        except Exception as e:
            logger.warning(f"Could not load draft cache: {e}")

    total_tokens = {"prompt": 0, "completion": 0, "total": 0}

    def add_tokens(tok: Dict[str, int]):
        total_tokens["prompt"] += tok.get("prompt", 0)
        total_tokens["completion"] += tok.get("completion", 0)
        total_tokens["total"] += tok.get("total", 0)

    # Step 1: Generate 24 Candidates
    logger.info("=== STEP 1: GENERATING 24 CANDIDATE QUESTIONS ===")
    candidates = []

    for cfg in CANDIDATE_CONFIGS:
        cid = cfg["candidate_id"]
        pid = cfg["product_id"]
        qtype = cfg["qtype"]
        is_hinglish = cfg["is_hinglish"]
        cat = cfg["category"]
        product = products[pid]
        p_chunks = chunks_by_pid.get(pid, [])

        cached_entry = draft_cache.get(cid)
        if cached_entry and not args.force and cached_entry.get("question"):
            q_text = cached_entry["question"]
            add_tokens(cached_entry.get("draft_tokens", {}))
            logger.info(f"[{cid}] ({cat} | {qtype} | {pid}): Loaded from cache: \"{q_text}\"")
        else:
            if qtype == "spec":
                q_text, tok = draft_spec_question(aoai_client, deployment, product, is_hinglish)
            else:
                q_text, tok = draft_procedural_question(aoai_client, deployment, product, p_chunks, is_hinglish)
            add_tokens(tok)
            draft_cache[cid] = {"question": q_text, "draft_tokens": tok}
            logger.info(f"[{cid}] ({cat} | {qtype} | {pid}): Generated: \"{q_text}\" (Tokens: {tok['total']})")

        candidates.append({
            "candidate_id": cid,
            "category": cat,
            "product_id": pid,
            "product_name": product.get("name"),
            "qtype": qtype,
            "is_hinglish": is_hinglish,
            "question": q_text,
        })

    # Step 2: N-gram overlap check (4-gram rejection)
    logger.info("\n=== STEP 2: N-GRAM OVERLAP FILTER (4-gram run with any chunk) ===")
    surviving_ngram = []
    rejected_by_ngram = []

    for c in candidates:
        pid = c["product_id"]
        p_chunks = chunks_by_pid.get(pid, [])
        overlap = check_ngram_overlap(c["question"], p_chunks, n=4)
        if overlap:
            matched_gram, matched_cid = overlap
            logger.warning(f"[{c['candidate_id']}] REJECTED BY N-GRAM: \"{matched_gram}\" matches chunk {matched_cid}")
            rejected_by_ngram.append({**c, "rejection_reason": f"Shared 4-gram '{matched_gram}' with {matched_cid}"})
        else:
            surviving_ngram.append(c)

    logger.info(f"Surviving N-gram filter: {len(surviving_ngram)} / {len(candidates)} (Rejected: {len(rejected_by_ngram)})")

    # Step 3: Strict Labeler Verification (same prompt logic as propose_labels.py)
    logger.info("\n=== STEP 3: STRICT LABELER VERIFICATION ===")
    surviving_labeled = []
    rejected_by_labeler = []

    for c in surviving_ngram:
        cid = c["candidate_id"]
        pid = c["product_id"]
        product = products[pid]
        p_chunks = chunks_by_pid.get(pid, [])
        qtype = c["qtype"]
        q_text = c["question"]

        cached_label = draft_cache.get(cid, {}).get("label_proposal")
        if cached_label and not args.force and cached_label.get("answerable") is not None:
            proposal = cached_label
            add_tokens(draft_cache[cid].get("label_tokens", {}))
            logger.info(f"[{cid}] Strict labeler (cached): Answerable={proposal.get('answerable')}")
        else:
            proposal, tok = call_llm_for_label(aoai_client, deployment, product, p_chunks, q_text, qtype)
            add_tokens(tok)
            draft_cache[cid]["label_proposal"] = proposal
            draft_cache[cid]["label_tokens"] = tok
            logger.info(f"[{cid}] Strict labeler: Answerable={proposal.get('answerable')} (Tokens: {tok['total']})")

        is_ans = bool(proposal.get("answerable"))
        cids = proposal.get("gold_chunk_ids", [])
        raw_kws = proposal.get("gold_keywords", [])
        valid_chunk_ids = {ck["chunk_id"] for ck in p_chunks}
        gold_cids = [cid_item for cid_item in cids if cid_item in valid_chunk_ids][:3]

        # Sanitize keywords for spec
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

        if is_ans and gold_cids:
            surviving_labeled.append({
                **c,
                "gold_chunk_ids": gold_cids,
                "gold_keywords": valid_kws if qtype == "spec" else [],
                "reason": proposal.get("reason", ""),
            })
        else:
            reason = proposal.get("reason", "Not directly answerable or missing gold chunk IDs")
            logger.warning(f"[{cid}] REJECTED BY LABELER: {reason}")
            rejected_by_labeler.append({**c, "rejection_reason": reason})

    logger.info(f"Surviving Labeler: {len(surviving_labeled)} / {len(surviving_ngram)} (Rejected: {len(rejected_by_labeler)})")

    # Save draft cache
    with open(DRAFT_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(draft_cache, f, indent=2, ensure_ascii=False)

    # Step 4: Selection (8 spec + 8 procedural, 4 dev + 4 test each, spread across categories)
    logger.info("\n=== STEP 4: SELECTING 16 QUESTIONS (8 spec + 8 procedural, 4 dev + 4 test each) ===")
    spec_survivors = [c for c in surviving_labeled if c["qtype"] == "spec"]
    proc_survivors = [c for c in surviving_labeled if c["qtype"] == "procedural"]

    categories = ["headphones", "chairs", "shoes", "watches"]

    selected_spec = []
    selected_proc = []

    # Select 2 spec per category (1 dev, 1 test)
    for cat in categories:
        cat_specs = [c for c in spec_survivors if c["category"] == cat]
        if len(cat_specs) < 2:
            logger.warning(f"Shortfall in spec for {cat}: only {len(cat_specs)} survivors")
            chosen = cat_specs
        else:
            chosen = cat_specs[:2]
        if len(chosen) >= 1:
            chosen[0]["split"] = "dev"
        if len(chosen) >= 2:
            chosen[1]["split"] = "test"
        selected_spec.extend(chosen)

    # Select 2 proc per category (1 dev, 1 test)
    for cat in categories:
        cat_procs = [c for c in proc_survivors if c["category"] == cat]
        if len(cat_procs) < 2:
            logger.warning(f"Shortfall in procedural for {cat}: only {len(cat_procs)} survivors")
            chosen = cat_procs
        else:
            chosen = cat_procs[:2]
        if len(chosen) >= 1:
            chosen[0]["split"] = "dev"
        if len(chosen) >= 2:
            chosen[1]["split"] = "test"
        selected_proc.extend(chosen)

    selected_all = selected_spec[:8] + selected_proc[:8]
    selected_ids = {c["candidate_id"] for c in selected_all}
    discarded_surplus = [c for c in surviving_labeled if c["candidate_id"] not in selected_ids]

    logger.info(f"Total Selected: {len(selected_all)} (Spec: {len(selected_spec)}, Procedural: {len(selected_proc)})")
    logger.info(f"Counts: Candidates={len(candidates)}, Rejected by N-gram={len(rejected_by_ngram)}, Rejected by Labeler={len(rejected_by_labeler)}, Selected={len(selected_all)}, Discarded Surplus={len(discarded_surplus)}")

    # Step 5: Append to data/eval/rag_eval.csv as Q41 onward
    # Read existing 40 rows
    existing_rows = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            # Drop any existing rows Q41+ if re-running
            if int(r["id"].replace("Q", "")) <= 40:
                existing_rows.append(r)

    start_num = 41
    new_rows = []
    for idx, item in enumerate(selected_all):
        qid = f"Q{start_num + idx:02d}"
        item["id"] = qid
        notes_tokens = ["LLM-DRAFTED"]
        if item["is_hinglish"]:
            notes_tokens.append("hinglish")
        notes = " ".join(notes_tokens)

        new_row = {
            "id": qid,
            "split": item["split"],
            "question": item["question"],
            "product_id": item["product_id"],
            "qtype": item["qtype"],
            "gold_chunk_ids": "|".join(item["gold_chunk_ids"]),
            "gold_keywords": "|".join(item["gold_keywords"]) if item["qtype"] == "spec" else "",
            "notes": notes,
        }
        new_rows.append(new_row)

    combined_rows = existing_rows + new_rows

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "split", "question", "product_id", "qtype", "gold_chunk_ids", "gold_keywords", "notes"],
        )
        writer.writeheader()
        for r in combined_rows:
            writer.writerow(r)

    logger.info(f"Saved {len(combined_rows)} total rows to {CSV_PATH} (Added {len(new_rows)} rows)")

    # Step 6: Update label_review.md with LLM-drafted questions section
    append_llm_drafted_section_to_review(selected_all, all_chunks)
    logger.info(f"Updated {REVIEW_MD_PATH} with LLM-drafted questions section")


def append_llm_drafted_section_to_review(selected_questions: List[Dict[str, Any]], all_chunks: Dict[str, Dict[str, Any]]):
    """Appends section 3: LLM-drafted questions to label_review.md."""
    # Read existing content up to section 3
    existing_lines = []
    if REVIEW_MD_PATH.exists():
        with open(REVIEW_MD_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("## 3. LLM-Drafted Questions"):
                    break
                existing_lines.append(line)

    lines = [l for l in existing_lines]
    if not lines[-1].endswith("\n"):
        lines.append("\n")

    lines.append("\n## 3. LLM-Drafted Questions (Q41–Q56)\n\n")
    lines.append(
        "> **Notice**: These 16 questions were LLM-drafted with casual customer phrasing, verified for 0 4-gram overlap "
        "with product chunks, and verified as directly answerable via strict labeling logic against local product documents.\n\n"
    )

    for item in selected_questions:
        qid = item["id"]
        qtext = item["question"]
        pid = item["product_id"]
        pname = item["product_name"]
        qtype = item["qtype"]
        split = item["split"]
        notes = "LLM-DRAFTED" + (" hinglish" if item["is_hinglish"] else "")
        g_cids = item["gold_chunk_ids"]
        kws = "|".join(item["gold_keywords"]) if item["gold_keywords"] else "None"
        reason = item.get("reason", "")

        lines.append(f"### [{qid}] {qtext}\n")
        lines.append(f"- **Split**: `{split}`\n")
        lines.append(f"- **Question Type**: `{qtype}`\n")
        lines.append(f"- **Product**: {pid} ({pname})\n")
        lines.append(f"- **Notes**: `{notes}`\n")
        lines.append(f"- **Model Annotation Reason**: *{reason}*\n")
        if qtype == "spec":
            lines.append(f"- **Gold Keywords**: `{kws}`\n")
        lines.append(f"- **Gold Chunk IDs**: `{ '|'.join(g_cids) }`\n\n")
        lines.append("**Proposed Chunk Snippets (first 300 chars):**\n")
        for cid in g_cids:
            chunk = all_chunks.get(cid, {})
            sec = chunk.get("section", "doc")
            title = chunk.get("title", "")
            raw_c = chunk.get("content", "").replace("\n", " ")
            snippet = raw_c[:300] + ("..." if len(raw_c) > 300 else "")
            lines.append(f"  * **`{cid}`** ({sec} - {title}): \"{snippet}\"\n")
        lines.append("\n---\n\n")

    with open(REVIEW_MD_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)


if __name__ == "__main__":
    main()
