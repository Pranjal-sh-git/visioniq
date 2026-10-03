"""tests/test_eval_metrics.py - Unit tests for RAG retrieval evaluation metrics computation.

Verifies:
1. In-memory fixture with 2 answerable rows (one hit at rank 1, one miss) + 1 unknown_product row.
2. Asserts Recall@1 == 0.5 and N answerable == 2 (unknown_product is excluded from denominator).
3. Score separability handles empty groups by returning 'no rows'.
"""

import pytest
from scripts.eval_rag import (
    compute_retrieval_metrics,
    format_score_stats,
    score_retrieval_ranks,
)


@pytest.fixture
def eval_fixture_rows():
    """Tiny in-memory fixture: 2 answerable rows + 1 unknown_product row."""
    return [
        # Row 1: Answerable (spec), Hit at rank 1
        {
            "id": "T001",
            "split": "dev",
            "question": "What is the battery life?",
            "product_id": "P001",
            "qtype": "spec",
            "gold_chunk_ids": {"P001_chunk_001"},
            "modes": {
                "vector": {"rec_1": 1.0, "rec_3": 1.0, "rec_5": 1.0, "rr": 1.0},
                "bm25": {"rec_1": 1.0, "rec_3": 1.0, "rec_5": 1.0, "rr": 1.0},
                "hybrid": {"rec_1": 1.0, "rec_3": 1.0, "rec_5": 1.0, "rr": 1.0},
                "hybrid+semantic": {"rec_1": 1.0, "rec_3": 1.0, "rec_5": 1.0, "rr": 1.0},
            },
        },
        # Row 2: Answerable (procedural), Miss (all ranks 0)
        {
            "id": "T002",
            "split": "dev",
            "question": "How do I clean the shoes?",
            "product_id": "P019",
            "qtype": "procedural",
            "gold_chunk_ids": {"P019_chunk_002"},
            "modes": {
                "vector": {"rec_1": 0.0, "rec_3": 0.0, "rec_5": 0.0, "rr": 0.0},
                "bm25": {"rec_1": 0.0, "rec_3": 0.0, "rec_5": 0.0, "rr": 0.0},
                "hybrid": {"rec_1": 0.0, "rec_3": 0.0, "rec_5": 0.0, "rr": 0.0},
                "hybrid+semantic": {"rec_1": 0.0, "rec_3": 0.0, "rec_5": 0.0, "rr": 0.0},
            },
        },
        # Row 3: Unanswerable (unknown_product), Must NOT enter denominator
        {
            "id": "T003",
            "split": "dev",
            "question": "Does this vintage camera use 600 film?",
            "product_id": "",
            "qtype": "unknown_product",
            "gold_chunk_ids": set(),
            "modes": {
                "vector": {"rec_1": 0.0, "rec_3": 0.0, "rec_5": 0.0, "rr": 0.0},
                "bm25": {"rec_1": 0.0, "rec_3": 0.0, "rec_5": 0.0, "rr": 0.0},
                "hybrid": {"rec_1": 0.0, "rec_3": 0.0, "rec_5": 0.0, "rr": 0.0},
                "hybrid+semantic": {"rec_1": 0.0, "rec_3": 0.0, "rec_5": 0.0, "rr": 0.0},
            },
        },
    ]


def test_answerable_denominator_and_recall1(eval_fixture_rows):
    """Assert Recall@1 = 0.5 and N answerable = 2 when unknown_product is present."""
    metrics = compute_retrieval_metrics(eval_fixture_rows, modes=["vector", "bm25", "hybrid", "hybrid+semantic"])

    # 1. Denominator check
    assert metrics["n_answerable"] == 2
    assert metrics["total_rows"] == 3

    # 2. Recall@1 check: 1 hit out of 2 answerable rows = 0.5 (NOT 1/3 = 0.333)
    assert metrics["modes"]["vector"]["mean_rec_1"] == 0.5
    assert metrics["modes"]["bm25"]["mean_rec_1"] == 0.5
    assert metrics["modes"]["hybrid"]["mean_rec_1"] == 0.5
    assert metrics["modes"]["hybrid+semantic"]["mean_rec_1"] == 0.5

    # 3. MRR check: (1.0 + 0.0) / 2 = 0.5
    assert metrics["modes"]["vector"]["mean_mrr"] == 0.5


def test_score_retrieval_ranks():
    """Verify rank scoring logic for hits and misses."""
    gold = {"chunk_A", "chunk_B"}

    # Hit at rank 0 (top 1)
    res_rank0 = score_retrieval_ranks(["chunk_A", "other_1", "other_2"], gold, top_k=5)
    assert res_rank0["rec_1"] == 1.0
    assert res_rank0["rec_3"] == 1.0
    assert res_rank0["rec_5"] == 1.0
    assert res_rank0["rr"] == 1.0

    # Hit at rank 2 (3rd item)
    res_rank2 = score_retrieval_ranks(["other_1", "other_2", "chunk_B"], gold, top_k=5)
    assert res_rank2["rec_1"] == 0.0
    assert res_rank2["rec_3"] == 1.0
    assert res_rank2["rec_5"] == 1.0
    assert res_rank2["rr"] == pytest.approx(1.0 / 3.0)

    # Completely unanswerable / empty gold chunk set
    res_empty = score_retrieval_ranks(["other_1", "other_2"], set(), top_k=5)
    assert res_empty["rec_1"] == 0.0
    assert res_empty["rec_5"] == 0.0
    assert res_empty["rr"] == 0.0


def test_format_score_stats_empty_group():
    """Verify format_score_stats outputs 'no rows' for empty groups."""
    empty_stats = {"count": 0, "mean": 0.0, "min": 0.0, "max": 0.0, "median": 0.0}
    assert format_score_stats(empty_stats) == "no rows"

    populated_stats = {"count": 2, "mean": 0.75, "min": 0.5, "max": 1.0, "median": 0.75}
    assert format_score_stats(populated_stats) == "0.7500 [0.5000, 1.0000]"
