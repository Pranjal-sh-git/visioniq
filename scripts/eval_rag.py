"""scripts/eval_rag.py - RAG retrieval evaluation harness.

Evaluates retrieval quality on the product-chunks index across:
1. Vector (HNSW cosine)
2. BM25 (lexical)
3. Hybrid (RRF)
4. Hybrid + Semantic Reranker

Metrics & Rules:
- RAG Hit: Any gold chunk ID in top-k (exact chunk match).
- Denominator: Computed strictly over answerable rows with gold_chunk_ids (spec, procedural).
  out_of_docs and unknown_product rows NEVER enter the Recall/MRR denominator.
  Displays 'N answerable = x'.
- Per-QType breakdown: Dedicated tables for spec and procedural across all 4 modes.
- JSON Baseline: Evaluated on spec rows ONLY via products.json entry lookup against gold_keywords.
- Score Separability (dev only): Top-1 vector cosine and top-1 semantic reranker scores.
  Separates answerable (spec/procedural) vs unanswerable (out_of_docs, unknown_product reported separately).
  Prints 'no rows' for empty groups. If any group has < 5 rows, prints 'n too small, AUC not reported'.
- Filter: unknown_product rows run WITHOUT a product_id filter.
"""

import argparse
import csv
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
from sklearn.metrics import roc_auc_score

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure workspace root and backend are on sys.path
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
for directory in (str(ROOT_DIR), str(ROOT_DIR / "backend")):
    if directory not in sys.path:
        sys.path.insert(0, directory)

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType, VectorizedQuery

from backend.config import settings
from services.llm import get_azure_openai_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("visioniq.eval_rag")

ANSWERABLE_QTYPES = {"spec", "procedural"}
MODES = ["vector", "bm25", "hybrid", "hybrid+semantic"]


def compute_bootstrap_ci(
    values: List[float],
    n_bootstrap: int = 1000,
    confidence: float = 0.95,
    seed: int = 42,
) -> Tuple[float, float, float]:
    """Computes sample mean and 95% bootstrap confidence interval."""
    if not values:
        return 0.0, 0.0, 0.0
    mean_val = float(np.mean(values))
    if len(values) <= 1:
        return mean_val, mean_val, mean_val

    rng = np.random.RandomState(seed)
    indices = rng.randint(0, len(values), size=(n_bootstrap, len(values)))
    boot_means = np.mean(np.array(values)[indices], axis=1)
    alpha = (1.0 - confidence) / 2.0
    lower_pct = alpha * 100.0
    upper_pct = (1.0 - alpha) * 100.0
    ci_lower = float(np.percentile(boot_means, lower_pct))
    ci_upper = float(np.percentile(boot_means, upper_pct))
    return mean_val, ci_lower, ci_upper


def format_metric(mean: float, ci_lower: float, ci_upper: float) -> str:
    """Formats mean and CI bounds."""
    return f"{mean:.3f} [{ci_lower:.3f}, {ci_upper:.3f}]"


def format_score_stats(stats: Dict[str, Any]) -> str:
    """Formats score distribution or 'no rows' if empty."""
    if stats["count"] == 0:
        return "no rows"
    return f"{stats['mean']:.4f} [{stats['min']:.4f}, {stats['max']:.4f}]"


def score_retrieval_ranks(retrieved_chunk_ids: List[str], gold_chunk_ids: Set[str], top_k: int = 5) -> Dict[str, float]:
    """Scores a single ranking against a set of gold chunk IDs."""
    hits = [cid in gold_chunk_ids for cid in retrieved_chunk_ids[:top_k]]
    while len(hits) < top_k:
        hits.append(False)
    rec_1 = 1.0 if any(hits[:1]) else 0.0
    rec_3 = 1.0 if any(hits[:3]) else 0.0
    rec_5 = 1.0 if any(hits[:5]) else 0.0
    rr = 0.0
    for idx, hit in enumerate(hits):
        if hit:
            rr = 1.0 / (idx + 1)
            break
    return {"rec_1": rec_1, "rec_3": rec_3, "rec_5": rec_5, "rr": rr}


def compute_retrieval_metrics(
    eval_rows: List[Dict[str, Any]],
    modes: List[str] = ("vector", "bm25", "hybrid", "hybrid+semantic"),
    n_bootstrap: int = 1000,
    seed: int = 42,
) -> Dict[str, Any]:
    """Computes retrieval metrics strictly over answerable rows with gold_chunk_ids.

    Excludes out_of_docs and unknown_product from the denominator.
    """
    answerable_rows = [
        r for r in eval_rows
        if bool(r.get("gold_chunk_ids")) and r.get("qtype") in ANSWERABLE_QTYPES
    ]
    n_answerable = len(answerable_rows)

    metrics_by_mode = {}
    for m in modes:
        if n_answerable == 0:
            metrics_by_mode[m] = {
                "rec_1": (0.0, 0.0, 0.0),
                "rec_3": (0.0, 0.0, 0.0),
                "rec_5": (0.0, 0.0, 0.0),
                "mrr": (0.0, 0.0, 0.0),
                "mean_rec_1": 0.0,
                "mean_rec_3": 0.0,
                "mean_rec_5": 0.0,
                "mean_mrr": 0.0,
                "count": 0,
            }
        else:
            r1_vals = [r["modes"][m]["rec_1"] for r in answerable_rows]
            r3_vals = [r["modes"][m]["rec_3"] for r in answerable_rows]
            r5_vals = [r["modes"][m]["rec_5"] for r in answerable_rows]
            mrr_vals = [r["modes"][m]["rr"] for r in answerable_rows]

            m_r1, l_r1, u_r1 = compute_bootstrap_ci(r1_vals, n_bootstrap, seed=seed)
            m_r3, l_r3, u_r3 = compute_bootstrap_ci(r3_vals, n_bootstrap, seed=seed)
            m_r5, l_r5, u_r5 = compute_bootstrap_ci(r5_vals, n_bootstrap, seed=seed)
            m_mrr, l_mrr, u_mrr = compute_bootstrap_ci(mrr_vals, n_bootstrap, seed=seed)

            metrics_by_mode[m] = {
                "rec_1": (m_r1, l_r1, u_r1),
                "rec_3": (m_r3, l_r3, u_r3),
                "rec_5": (m_r5, l_r5, u_r5),
                "mrr": (m_mrr, l_mrr, u_mrr),
                "mean_rec_1": m_r1,
                "mean_rec_3": m_r3,
                "mean_rec_5": m_r5,
                "mean_mrr": m_mrr,
                "count": n_answerable,
            }

    return {
        "n_answerable": n_answerable,
        "total_rows": len(eval_rows),
        "modes": metrics_by_mode,
    }


def get_embedding(client, text: str, deployment: str) -> List[float]:
    """Generates embedding for a text query."""
    resp = client.embeddings.create(input=[text], model=deployment)
    return resp.data[0].embedding


def load_products_catalog(products_path: Path) -> Dict[str, Dict[str, Any]]:
    """Loads products.json indexed by product ID."""
    if not products_path.exists():
        logger.warning(f"Products file not found at {products_path}")
        return {}
    with open(products_path, "r", encoding="utf-8") as f:
        items = json.load(f)
    return {p["id"]: p for p in items if "id" in p}


def format_product_catalog_context(product: Dict[str, Any]) -> str:
    """Formats products.json entry into text context matching baseline Q&A."""
    name = product.get("name", "")
    brand = product.get("brand", "")
    category = product.get("category", "")
    description = product.get("description", "")
    features = product.get("features", [])
    specs = product.get("specifications", {})

    features_str = " ".join(features)
    specs_str = " ".join(f"{k} {v}" for k, v in specs.items())
    return f"{brand} {name} {category} {description} {features_str} {specs_str}".lower()


def evaluate_query(
    search_client: SearchClient,
    question: str,
    query_vector: List[float],
    product_id: Optional[str],
    qtype: str,
    gold_chunk_ids: Set[str],
    top_k: int = 5,
) -> Dict[str, Any]:
    """Runs retrieval across 4 modes and evaluates gold chunk hits (no keyword matching)."""
    # unknown_product rows are run WITHOUT a product filter
    if qtype == "unknown_product" or not product_id:
        filter_expr = None
    else:
        filter_expr = f"product_id eq '{product_id}'"

    mode_results = {}
    top1_scores = {"vector_cosine": 0.0, "semantic_reranker": 0.0}

    for mode in MODES:
        if mode == "vector":
            vq = VectorizedQuery(vector=query_vector, k_nearest_neighbors=top_k, fields="content_vector")
            results = search_client.search(
                search_text=None,
                vector_queries=[vq],
                filter=filter_expr,
                top=top_k,
                select=["chunk_id"],
            )
        elif mode == "bm25":
            results = search_client.search(
                search_text=question,
                vector_queries=None,
                filter=filter_expr,
                top=top_k,
                select=["chunk_id"],
            )
        elif mode == "hybrid":
            vq = VectorizedQuery(vector=query_vector, k_nearest_neighbors=top_k, fields="content_vector")
            results = search_client.search(
                search_text=question,
                vector_queries=[vq],
                filter=filter_expr,
                top=top_k,
                select=["chunk_id"],
            )
        elif mode == "hybrid+semantic":
            vq = VectorizedQuery(vector=query_vector, k_nearest_neighbors=top_k, fields="content_vector")
            results = search_client.search(
                search_text=question,
                vector_queries=[vq],
                filter=filter_expr,
                query_type=QueryType.SEMANTIC,
                semantic_configuration_name="chunk-semantic-config",
                top=top_k,
                select=["chunk_id"],
            )

        retrieved_ids = []
        for rank, r in enumerate(results):
            cid = r.get("chunk_id", "")
            retrieved_ids.append(cid)
            if rank == 0:
                if mode == "vector":
                    top1_scores["vector_cosine"] = float(r.get("@search.score") or 0.0)
                elif mode == "hybrid+semantic":
                    top1_scores["semantic_reranker"] = float(r.get("@search.reranker_score") or 0.0)

        mode_results[mode] = score_retrieval_ranks(retrieved_ids, gold_chunk_ids, top_k=top_k)

    return {
        "modes": mode_results,
        "top1_scores": top1_scores,
    }


def compute_distribution_stats(scores: List[float]) -> Dict[str, Any]:
    """Computes count, mean, min, max, and median for a list of scores."""
    if not scores:
        return {"count": 0, "mean": 0.0, "min": 0.0, "max": 0.0, "median": 0.0}
    arr = np.array(scores)
    return {
        "count": len(scores),
        "mean": float(np.mean(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "median": float(np.median(arr)),
    }


def compute_auc_or_fallback(
    pos_scores: List[float],
    neg_scores: List[float],
    min_samples: int = 5,
) -> str:
    """Computes ROC AUC or returns 'n too small, AUC not reported' if count < min_samples."""
    if len(pos_scores) < min_samples or len(neg_scores) < min_samples:
        return "n too small, AUC not reported"

    labels = [1] * len(pos_scores) + [0] * len(neg_scores)
    scores = pos_scores + neg_scores

    if len(set(labels)) < 2:
        return "n too small, AUC not reported"

    try:
        score_val = float(roc_auc_score(labels, scores))
        return f"{score_val:.4f}"
    except Exception as e:
        logger.warning(f"Error computing AUC: {e}")
        return "n too small, AUC not reported"


def run_evaluation(
    csv_path: Path,
    output_md_path: Path,
    products_path: Path,
    top_k: int = 5,
    n_bootstrap: int = 1000,
    seed: int = 42,
) -> None:
    """Executes the full evaluation harness."""
    if not csv_path.exists():
        logger.error(f"Evaluation CSV not found at {csv_path}")
        sys.exit(1)

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        logger.error(f"No rows found in {csv_path}")
        sys.exit(1)

    logger.info(f"Loaded {len(rows)} evaluation questions from {csv_path}")

    # Load catalog for baseline lookup
    catalog = load_products_catalog(products_path)

    # Initialize Azure clients
    aoai_client = get_azure_openai_client()
    embedding_deployment = settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT or "text-embedding-3-small"
    index_name = settings.AZURE_SEARCH_CHUNKS_INDEX or "product-chunks"

    search_client = SearchClient(
        endpoint=settings.AZURE_SEARCH_ENDPOINT,
        index_name=index_name,
        credential=AzureKeyCredential(settings.AZURE_SEARCH_KEY),
    )

    eval_data = []
    for r in rows:
        qid = r.get("id", "").strip()
        split = r.get("split", "dev").strip().lower()
        question = r.get("question", "").strip()
        pid = r.get("product_id", "").strip()
        qtype = r.get("qtype", "").strip().lower()
        raw_chunk_ids = r.get("gold_chunk_ids", "").strip()
        raw_keywords = r.get("gold_keywords", "").strip()
        notes = r.get("notes", "").strip()

        gold_chunk_ids = set(c.strip() for c in raw_chunk_ids.split("|") if c.strip())
        gold_keywords = [k.strip().lower() for k in raw_keywords.split("|") if k.strip()]

        filter_status = "NO FILTER" if (qtype == "unknown_product" or not pid) else f"filter: {pid}"
        logger.info(f"Evaluating {qid} [{split} - {qtype}] ({filter_status}): \"{question}\"")
        q_vec = get_embedding(aoai_client, question, embedding_deployment)

        # Baseline: products.json entry lookup evaluated on SPEC rows only
        baseline_hit: Optional[float] = None
        if qtype == "spec":
            baseline_hit = 0.0
            if pid and pid in catalog:
                catalog_text = format_product_catalog_context(catalog[pid])
                if any(kw in catalog_text for kw in gold_keywords):
                    baseline_hit = 1.0

        res = evaluate_query(
            search_client=search_client,
            question=question,
            query_vector=q_vec,
            product_id=pid if pid else None,
            qtype=qtype,
            gold_chunk_ids=gold_chunk_ids,
            top_k=top_k,
        )

        eval_data.append({
            "id": qid,
            "split": split,
            "question": question,
            "product_id": pid,
            "qtype": qtype,
            "gold_chunk_ids": gold_chunk_ids,
            "gold_keywords": gold_keywords,
            "notes": notes,
            "baseline_hit": baseline_hit,
            "modes": res["modes"],
            "top1_scores": res["top1_scores"],
        })

    # Group by split
    splits = sorted(list(set(d["split"] for d in eval_data)))

    # Build report content with visible banner
    report_lines = []
    report_lines.append("# VisionIQ RAG Retrieval Evaluation Report\n")
    report_lines.append("> [!WARNING]")
    report_lines.append("> **PLACEHOLDER DATA, NOT RESULTS**: The metrics below are generated from placeholder evaluation rows to validate the evaluation pipeline mechanics. Real benchmark results will be produced once the full evaluation dataset is labeled.\n")
    report_lines.append("> [!NOTE]")
    report_lines.append("> LLM-drafted questions may overstate recall; human-written questions are reported separately.\n")
    report_lines.append(f"**Target Index**: `{index_name}`  ")
    report_lines.append(f"**Embedding Model**: `{embedding_deployment}`  ")
    report_lines.append(f"**Evaluated Questions**: {len(eval_data)}  ")
    report_lines.append(f"**Bootstrap Resamples**: {n_bootstrap} (95% CI)  \n")

    print("\n" + "=" * 80)
    print("VISIONIQ RAG RETRIEVAL EVALUATION RESULTS")
    print("=" * 80)

    for sp in splits:
        sp_data = [d for d in eval_data if d["split"] == sp]
        # REQUIREMENT 1: Compute metrics ONLY over answerable rows with gold_chunk_ids
        overall_res = compute_retrieval_metrics(sp_data, modes=MODES, n_bootstrap=n_bootstrap, seed=seed)
        n_ans = overall_res["n_answerable"]

        print(f"\n==================== SPLIT: {sp.upper()} (N answerable = {n_ans}, Total = {len(sp_data)}) ====================")
        report_lines.append(f"## Evaluation Split: `{sp.upper()}` (N answerable = {n_ans}, Total = {len(sp_data)})\n")

        # Overall retrieval performance
        print(f"\n--- Overall Retrieval Performance by Mode (N answerable = {n_ans}) ---")
        print(f"{'Mode':<18} | {'Recall@1 (95% CI)':<24} | {'Recall@3 (95% CI)':<24} | {'Recall@5 (95% CI)':<24} | {'MRR (95% CI)':<24}")
        print("-" * 120)

        report_lines.append(f"### Overall Retrieval Performance (N answerable = {n_ans})\n")
        report_lines.append(
            "> [!NOTE]\n"
            "> Retrieval metrics (Recall@k, MRR, CIs) are computed strictly over rows that have gold chunk IDs "
            "(`spec` and `procedural`). `out_of_docs` and `unknown_product` rows do not enter the Recall/MRR denominator.\n"
        )
        report_lines.append("| Retrieval Mode | Recall@1 [95% CI] | Recall@3 [95% CI] | Recall@5 [95% CI] | MRR [95% CI] |")
        report_lines.append("| :--- | :--- | :--- | :--- | :--- |")

        for m in MODES:
            m_dict = overall_res["modes"][m]
            if n_ans == 0:
                str_r1 = str_r3 = str_r5 = str_mrr = "no rows"
            else:
                str_r1 = format_metric(*m_dict["rec_1"])
                str_r3 = format_metric(*m_dict["rec_3"])
                str_r5 = format_metric(*m_dict["rec_5"])
                str_mrr = format_metric(*m_dict["mrr"])

            print(f"{m:<18} | {str_r1:<24} | {str_r3:<24} | {str_r5:<24} | {str_mrr:<24}")
            report_lines.append(f"| **{m}** | {str_r1} | {str_r3} | {str_r5} | {str_mrr} |")

        # Per-qtype table (spec / procedural) for each retrieval mode
        print("\n--- Per-QType Retrieval Performance by Mode (spec / procedural) ---")
        report_lines.append("\n### Per-QType Retrieval Performance Across Modes (spec / procedural)\n")
        report_lines.append("| Retrieval Mode | Question Type | N | Recall@1 [95% CI] | Recall@3 [95% CI] | Recall@5 [95% CI] | MRR [95% CI] |")
        report_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

        for m in MODES:
            print(f"\nMode: {m}")
            for qt in ("spec", "procedural"):
                qt_items = [d for d in sp_data if d["qtype"] == qt and bool(d["gold_chunk_ids"])]
                n_qt = len(qt_items)
                if n_qt == 0:
                    print(f"  * {qt:<12} (n=0): no rows")
                    report_lines.append(f"| **{m}** | `{qt}` | 0 | no rows | no rows | no rows | no rows |")
                else:
                    r1_vals = [d["modes"][m]["rec_1"] for d in qt_items]
                    r3_vals = [d["modes"][m]["rec_3"] for d in qt_items]
                    r5_vals = [d["modes"][m]["rec_5"] for d in qt_items]
                    mrr_vals = [d["modes"][m]["rr"] for d in qt_items]

                    m_r1, l_r1, u_r1 = compute_bootstrap_ci(r1_vals, n_bootstrap, seed=seed)
                    m_r3, l_r3, u_r3 = compute_bootstrap_ci(r3_vals, n_bootstrap, seed=seed)
                    m_r5, l_r5, u_r5 = compute_bootstrap_ci(r5_vals, n_bootstrap, seed=seed)
                    m_mrr, l_mrr, u_mrr = compute_bootstrap_ci(mrr_vals, n_bootstrap, seed=seed)

                    str_r1 = format_metric(m_r1, l_r1, u_r1)
                    str_r3 = format_metric(m_r3, l_r3, u_r3)
                    str_r5 = format_metric(m_r5, l_r5, u_r5)
                    str_mrr = format_metric(m_mrr, l_mrr, u_mrr)

                    print(f"  * {qt:<12} (n={n_qt}): Recall@1={str_r1} | Recall@5={str_r5} | MRR={str_mrr}")
                    report_lines.append(f"| **{m}** | `{qt}` | {n_qt} | {str_r1} | {str_r3} | {str_r5} | {str_mrr} |")

        # By-Origin table (Human-written vs LLM-drafted) for answerable rows
        print("\n--- Retrieval Performance by Origin (Human-written vs LLM-drafted) ---")
        report_lines.append("\n### Retrieval Performance by Question Origin (Answerable Rows Only)\n")
        report_lines.append("| Retrieval Mode | Question Origin | N | Recall@1 [95% CI] | Recall@3 [95% CI] | Recall@5 [95% CI] | MRR [95% CI] |")
        report_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

        ans_rows = [d for d in sp_data if bool(d["gold_chunk_ids"])]
        for m in MODES:
            print(f"\nMode: {m}")
            for origin_label, is_llm in (("Human-written", False), ("LLM-drafted", True)):
                orig_items = [d for d in ans_rows if ("LLM-DRAFTED" in d.get("notes", "")) == is_llm]
                n_orig = len(orig_items)
                if n_orig == 0:
                    print(f"  * {origin_label:<14} (n=0): no rows")
                    report_lines.append(f"| **{m}** | `{origin_label}` | 0 | no rows | no rows | no rows | no rows |")
                else:
                    r1_vals = [d["modes"][m]["rec_1"] for d in orig_items]
                    r3_vals = [d["modes"][m]["rec_3"] for d in orig_items]
                    r5_vals = [d["modes"][m]["rec_5"] for d in orig_items]
                    mrr_vals = [d["modes"][m]["rr"] for d in orig_items]

                    m_r1, l_r1, u_r1 = compute_bootstrap_ci(r1_vals, n_bootstrap, seed=seed)
                    m_r3, l_r3, u_r3 = compute_bootstrap_ci(r3_vals, n_bootstrap, seed=seed)
                    m_r5, l_r5, u_r5 = compute_bootstrap_ci(r5_vals, n_bootstrap, seed=seed)
                    m_mrr, l_mrr, u_mrr = compute_bootstrap_ci(mrr_vals, n_bootstrap, seed=seed)

                    str_r1 = format_metric(m_r1, l_r1, u_r1)
                    str_r3 = format_metric(m_r3, l_r3, u_r3)
                    str_r5 = format_metric(m_r5, l_r5, u_r5)
                    str_mrr = format_metric(m_mrr, l_mrr, u_mrr)

                    print(f"  * {origin_label:<14} (n={n_orig}): Recall@1={str_r1} | Recall@5={str_r5} | MRR={str_mrr}")
                    report_lines.append(f"| **{m}** | `{origin_label}` | {n_orig} | {str_r1} | {str_r3} | {str_r5} | {str_mrr} |")

        # Baseline Comparison (SPEC ONLY)
        spec_data = [d for d in sp_data if d["qtype"] == "spec"]
        print("\n--- JSON Catalog Baseline vs RAG (Evaluated on 'spec' Rows Only) ---")
        report_lines.append("\n### Baseline (JSON Lookup) vs RAG (Evaluated on 'spec' Rows Only)\n")
        report_lines.append(
            "> [!NOTE]\n"
            "> The JSON catalog baseline is evaluated strictly on `spec` questions via `gold_keywords`. "
            "`procedural` questions are omitted as procedural guidance is absent from catalog JSON; "
            "`out_of_docs` and `unknown_product` have no gold catalog answers.\n"
        )
        report_lines.append("| Question Type | Total Queries | Baseline (JSON Lookup Recall) | RAG Hybrid+Semantic Recall@5 |")
        report_lines.append("| :--- | :--- | :--- | :--- |")

        if spec_data:
            base_vals = [d["baseline_hit"] for d in spec_data if d["baseline_hit"] is not None]
            rag_vals = [d["modes"]["hybrid+semantic"]["rec_5"] for d in spec_data]

            m_b, l_b, u_b = compute_bootstrap_ci(base_vals, n_bootstrap, seed=seed)
            m_r, l_r, u_r = compute_bootstrap_ci(rag_vals, n_bootstrap, seed=seed)

            b_str = format_metric(m_b, l_b, u_b)
            r_str = format_metric(m_r, l_r, u_r)

            print(f"spec (n={len(spec_data)}): Baseline={b_str} vs RAG Hybrid+Semantic={r_str}")
            report_lines.append(f"| `spec` | {len(spec_data)} | {b_str} | {r_str} |")
        else:
            print("No 'spec' rows in this split.")
            report_lines.append("| `spec` | 0 | no rows | no rows |")

        # Score Separability (Dev Only) - REQUIREMENT 2: print 'no rows' for empty groups
        if sp == "dev":
            print("\n--- Score Separability & Separation AUC (Dev Only) ---")
            report_lines.append("\n### Score Separability (Dev Only)\n")
            report_lines.append(
                "> [!NOTE]\n"
                "> Evaluates separation between **Answerable** (`spec`, `procedural`) and **Unanswerable** "
                "(`out_of_docs`, `unknown_product`). If any group has fewer than 5 rows, 'n too small, AUC not reported' is returned.\n"
            )

            ans_items = [d for d in sp_data if d["qtype"] in ANSWERABLE_QTYPES]
            ood_items = [d for d in sp_data if d["qtype"] == "out_of_docs"]
            unk_items = [d for d in sp_data if d["qtype"] == "unknown_product"]

            ans_vec = [d["top1_scores"]["vector_cosine"] for d in ans_items]
            ans_sem = [d["top1_scores"]["semantic_reranker"] for d in ans_items]

            ood_vec = [d["top1_scores"]["vector_cosine"] for d in ood_items]
            ood_sem = [d["top1_scores"]["semantic_reranker"] for d in ood_items]

            unk_vec = [d["top1_scores"]["vector_cosine"] for d in unk_items]
            unk_sem = [d["top1_scores"]["semantic_reranker"] for d in unk_items]

            stats_ans_vec = compute_distribution_stats(ans_vec)
            stats_ans_sem = compute_distribution_stats(ans_sem)
            stats_ood_vec = compute_distribution_stats(ood_vec)
            stats_ood_sem = compute_distribution_stats(ood_sem)
            stats_unk_vec = compute_distribution_stats(unk_vec)
            stats_unk_sem = compute_distribution_stats(unk_sem)

            print(f"Answerable queries (n={len(ans_items)}):")
            print(f"  * Top-1 Vector Cosine    : {format_score_stats(stats_ans_vec)}")
            print(f"  * Top-1 Semantic Reranker: {format_score_stats(stats_ans_sem)}")

            print(f"Unanswerable - Out of Docs (n={len(ood_items)}):")
            print(f"  * Top-1 Vector Cosine    : {format_score_stats(stats_ood_vec)}")
            print(f"  * Top-1 Semantic Reranker: {format_score_stats(stats_ood_sem)}")

            print(f"Unanswerable - Unknown Product (n={len(unk_items)}):")
            print(f"  * Top-1 Vector Cosine    : {format_score_stats(stats_unk_vec)}")
            print(f"  * Top-1 Semantic Reranker: {format_score_stats(stats_unk_sem)}")

            auc_ood_vec = compute_auc_or_fallback(ans_vec, ood_vec, min_samples=5)
            auc_ood_sem = compute_auc_or_fallback(ans_sem, ood_sem, min_samples=5)

            auc_unk_vec = compute_auc_or_fallback(ans_vec, unk_vec, min_samples=5)
            auc_unk_sem = compute_auc_or_fallback(ans_sem, unk_sem, min_samples=5)

            print("\nSeparation AUC (Answerable vs Out-of-Docs):")
            print(f"  * Vector Cosine AUC      : {auc_ood_vec}")
            print(f"  * Semantic Reranker AUC  : {auc_ood_sem}")

            print("Separation AUC (Answerable vs Unknown-Product):")
            print(f"  * Vector Cosine AUC      : {auc_unk_vec}")
            print(f"  * Semantic Reranker AUC  : {auc_unk_sem}")

            report_lines.append("| Target Group Comparison | Score Type | Answerable (Mean [Min, Max]) | Unanswerable (Mean [Min, Max]) | Separation ROC AUC |")
            report_lines.append("| :--- | :--- | :--- | :--- | :--- |")
            report_lines.append(
                f"| **Answerable vs Out-of-Docs** | Top-1 Vector Cosine | {format_score_stats(stats_ans_vec)} | {format_score_stats(stats_ood_vec)} | {auc_ood_vec} |"
            )
            report_lines.append(
                f"| **Answerable vs Out-of-Docs** | Top-1 Semantic Reranker | {format_score_stats(stats_ans_sem)} | {format_score_stats(stats_ood_sem)} | {auc_ood_sem} |"
            )
            report_lines.append(
                f"| **Answerable vs Unknown-Product** | Top-1 Vector Cosine | {format_score_stats(stats_ans_vec)} | {format_score_stats(stats_unk_vec)} | {auc_unk_vec} |"
            )
            report_lines.append(
                f"| **Answerable vs Unknown-Product** | Top-1 Semantic Reranker | {format_score_stats(stats_ans_sem)} | {format_score_stats(stats_unk_sem)} | {auc_unk_sem} |"
            )
            report_lines.append("")

    # Save output
    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    logger.info(f"RAG evaluation report successfully saved to {output_md_path}")
    print("\n" + "=" * 80)
    print(f"Report saved to: {output_md_path}")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Evaluate RAG retrieval performance.")
    parser.add_argument("--csv", type=Path, default=ROOT_DIR / "data" / "eval" / "rag_eval.csv", help="Path to evaluation CSV")
    parser.add_argument("--output-md", type=Path, default=ROOT_DIR / "docs" / "rag_eval_results.md", help="Path to output markdown report")
    parser.add_argument("--products", type=Path, default=ROOT_DIR / "data" / "products" / "products.json", help="Path to products.json")
    parser.add_argument("--top-k", type=int, default=5, help="Number of retrieved chunks")
    parser.add_argument("--bootstrap", type=int, default=1000, help="Number of bootstrap iterations for CI")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for bootstrap")
    args = parser.parse_args()

    run_evaluation(
        csv_path=args.csv,
        output_md_path=args.output_md,
        products_path=args.products,
        top_k=args.top_k,
        n_bootstrap=args.bootstrap,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
