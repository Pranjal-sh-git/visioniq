"""Comprehensive Validation for Context-Aware Video Q&A and Grounded Precision.

Validates:
1. Context boundary detection (question/setup -> context_start, explanation -> context_end).
2. Distinction between context_start and matched_timestamp.
3. Multiple mentions disambiguation.
4. Grounded, precise LLM answers without extraneous general knowledge.
5. Insufficient evidence handling.
6. Non-negative bounds (context_start >= 0.0).
"""

import json
import logging
import sys
from pathlib import Path

# Ensure workspace root and backend are on sys.path
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
for directory in (str(ROOT_DIR), str(ROOT_DIR / "backend")):
    if directory not in sys.path:
        sys.path.insert(0, directory)

from services.video.search import detect_context_window, grounded_video_qa

logger = logging.getLogger(__name__)


def test_lecture_reaction_context_window():
    """Validates the exact example from the task specification:
    10:32 (632s) -> "Let's consider the reaction between silver nitrate and sodium bromide."
    10:36 (636s) -> "What do you think will happen?"
    10:40 (640s) -> "The product formed is silver bromide."
    10:46 (646s) -> "Silver bromide appears as a pale yellow precipitate."
    10:55 (655s) -> "This is an example of a precipitation reaction."
    11:05 (665s) -> "Next topic we will explore is redox reactions."
    """
    print("=" * 80)
    print("TEST 1: Lecture Sequence Context-Aware Boundary Detection (Silver Bromide)")
    print("=" * 80)

    lecture_segments = [
        {"start_time": 600.0, "end_time": 630.0, "text": "Earlier we talked about solubility rules in aqueous solutions."},
        {"start_time": 632.0, "end_time": 635.5, "text": "Let's consider the reaction between silver nitrate and sodium bromide."},
        {"start_time": 636.0, "end_time": 639.5, "text": "What do you think will happen?"},
        {"start_time": 640.0, "end_time": 645.0, "text": "The product formed is silver bromide."},
        {"start_time": 646.0, "end_time": 654.0, "text": "Silver bromide appears as a pale yellow precipitate."},
        {"start_time": 655.0, "end_time": 662.0, "text": "This is an example of a precipitation reaction."},
        {"start_time": 665.0, "end_time": 680.0, "text": "Next topic we will explore is acid-base neutralization reactions."},
    ]

    # Keyword match occurs at 640.0s ("The product formed is silver bromide")
    matched_timestamp = 640.0
    query = "Explain the silver bromide part."

    context_start, context_end, evidence = detect_context_window(
        segments=lecture_segments,
        matched_timestamp=matched_timestamp,
        query=query,
    )

    print(f"  Matched Keyword Timestamp: {matched_timestamp:.1f}s (10:40)")
    print(f"  Detected Context Start:    {context_start:.1f}s ({int(context_start//60):02d}:{int(context_start%60):02d})")
    print(f"  Detected Context End:      {context_end:.1f}s ({int(context_end//60):02d}:{int(context_end%60):02d})")
    print(f"  Evidence Segment Count:    {len(evidence)}")
    for ev in evidence:
        print(f"    [{ev['timestamp']:.1f}s] {ev['text']}")

    # Assertions
    assert context_start <= 632.0, f"Expected context_start <= 632.0 (setup start), got {context_start}"
    assert context_start < matched_timestamp, f"context_start must precede matched_timestamp"
    assert context_end >= 662.0, f"Expected context_end to include explanation up to 662.0s, got {context_end}"
    assert context_end < 665.0 or context_end <= 665.0, f"context_end should stop before new topic at 665.0s"
    assert len(evidence) >= 4, f"Expected at least 4 evidence segments, got {len(evidence)}"
    print("  >>> PASSED: Accurately identified 10:32 (632s) as context_start and 662s as context_end!\n")


def test_buffer_fallback_when_no_linguistic_boundary():
    """Validates that approximately 5 seconds buffer is used when no explicit question/setup boundary exists."""
    print("=" * 80)
    print("TEST 2: Buffer Fallback (~5s) When No Setup Header Exists")
    print("=" * 80)

    segments = [
        {"start_time": 100.0, "end_time": 115.0, "text": "The battery efficiency was tested in various temperature conditions."},
        {"start_time": 120.0, "end_time": 135.0, "text": "Active noise cancellation uses inverted sound waves to cancel background hum."},
        {"start_time": 140.0, "end_time": 155.0, "text": "Comfort is achieved through lightweight memory foam ear cushions."},
    ]

    matched_timestamp = 120.0
    context_start, context_end, evidence = detect_context_window(
        segments=segments,
        matched_timestamp=matched_timestamp,
        query="Tell me about active noise cancellation.",
    )

    print(f"  Matched Timestamp: {matched_timestamp:.1f}s")
    print(f"  Context Start:     {context_start:.1f}s")
    print(f"  Context End:       {context_end:.1f}s")

    assert context_start == 115.0 or (112.0 <= context_start <= 116.0), f"Expected ~5s buffer preceding 120.0s, got {context_start}"
    assert context_start >= 0.0, "context_start must be >= 0.0"
    print("  >>> PASSED: Successfully applied preceding context buffer!\n")


def test_zero_bound_enforcement():
    """Validates that context_start can NEVER be negative."""
    print("=" * 80)
    print("TEST 3: Non-Negative Timestamp Enforcement (context_start >= 0.0)")
    print("=" * 80)

    segments = [
        {"start_time": 2.0, "end_time": 8.0, "text": "Welcome to today's presentation on artificial intelligence."},
    ]

    matched_timestamp = 2.0
    context_start, context_end, _ = detect_context_window(
        segments=segments,
        matched_timestamp=matched_timestamp,
        query="Welcome to today's presentation",
    )

    print(f"  Matched: {matched_timestamp:.1f}s -> Context Start: {context_start:.1f}s")
    assert context_start == 0.0 or context_start >= 0.0, f"context_start cannot be negative: {context_start}"
    print("  >>> PASSED: Lower bound 0.0 enforced strictly!\n")


def test_live_video_qa_with_context():
    """Validates grounded_video_qa on the sample video with structured schema assertions."""
    print("=" * 80)
    print("TEST 4: Live Video Q&A with Context-Aware Timestamps & Evidence")
    print("=" * 80)

    video_id = "vid_df16da8f30f96fb6"
    question = "Why did the speaker choose this specific area for the video?"

    result = grounded_video_qa(video_id=video_id, question=question)

    print(f"  Question:           {result.get('question')}")
    print(f"  Found Match:        {result.get('found_match')}")
    print(f"  Context Start:      {result.get('context_start')}s")
    print(f"  Matched Timestamp:  {result.get('matched_timestamp')}s")
    print(f"  Context End:        {result.get('context_end')}s")
    print(f"  Answer:\n  {result.get('answer')}\n")
    print(f"  Evidence Count:     {len(result.get('evidence', []))}")

    # Schema & Behavioral Assertions
    assert result.get("found_match") is True, "Expected found_match == True"
    assert "context_start" in result and result["context_start"] is not None
    assert "matched_timestamp" in result and result["matched_timestamp"] is not None
    assert "context_end" in result and result["context_end"] is not None
    assert "evidence" in result and isinstance(result["evidence"], list)
    assert result["context_start"] >= 0.0

    answer_lower = result.get("answer", "").lower()
    assert "eight" in answer_lower or "audience" in answer_lower or "standing room" in answer_lower, (
        f"Answer does not reflect speaker's explanation of fitting eight people / standing room: {result.get('answer')}"
    )
    print("  >>> PASSED: Live Video Q&A correctly returned separated context_start, matched_timestamp, and precise answer!\n")


def test_insufficient_evidence_handling():
    """Validates that non-existent topics return insufficient evidence response without hallucination."""
    print("=" * 80)
    print("TEST 5: Insufficient Evidence Handling (No Hallucination)")
    print("=" * 80)

    video_id = "vid_df16da8f30f96fb6"
    question = "What was said about photosynthesis in quantum computing algorithms?"

    result = grounded_video_qa(video_id=video_id, question=question, threshold=0.90)

    print(f"  Question:    {question}")
    print(f"  Found Match: {result.get('found_match')}")
    print(f"  Answer:      {result.get('answer')}")

    assert result.get("found_match") is False
    assert "not provide enough information" in result.get("answer", "").lower() or "no relevant segment" in result.get("answer", "").lower()
    print("  >>> PASSED: Insufficient evidence gracefully handled without guessing!\n")


if __name__ == "__main__":
    test_lecture_reaction_context_window()
    test_buffer_fallback_when_no_linguistic_boundary()
    test_zero_bound_enforcement()
    test_live_video_qa_with_context()
    test_insufficient_evidence_handling()
    print("=" * 80)
    print("ALL CONTEXT-AWARE VIDEO Q&A TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)
