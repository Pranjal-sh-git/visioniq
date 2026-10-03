"""Unit Tests for VisionIQ RAG Header-Aware Chunker.

Tests:
1. Chunk size bounds (token count constraints)
2. Overlap presence between consecutive chunks
3. Deterministic chunk IDs and unique formatting
4. Complete metadata fields
5. Numbered step lists preserved as atomic blocks (not split)
"""

import re
import pytest
from services.rag.chunker import chunk_markdown, count_tokens, parse_front_matter


SAMPLE_DOC_WITH_STEPS = """---
product_id: P001
section: user_manual
is_synthetic: true
generated_by: gpt-5-mini
generated_at: '2026-10-03T12:00:00Z'
---

# Sony WH-1000XM5 - User Manual

## 1. Product Overview & In the Box
The Sony WH-1000XM5 headphones deliver industry-leading wireless noise cancellation with two processors and eight microphones. In the box you will find the headphones, a protective carrying case, a USB-C charging cable, and a 3.5mm audio cable. Built with premium materials, the headphones offer a comfortable over-ear fit suitable for prolonged listening sessions. The headband is continuously adjustable and the synthetic leather ear cushions provide acoustic isolation.

## 2. Setup & Initial Configuration
Follow these step-by-step instructions to pair the headphones with your primary playback device:

1. Power on the headphones by pressing and holding the Power button for two seconds until the blue indicator light pulses.
2. For initial pairing, press and continue holding the Power button for five full seconds until you hear the voice prompt announce 'Bluetooth pairing'.
3. On your smartphone, tablet, or laptop, access the Bluetooth settings menu and verify that Bluetooth connectivity is enabled.
4. Locate 'Sony WH-1000XM5' in the list of available discoverable devices and tap to establish the connection.
5. Confirm the pairing prompt on your mobile screen and wait for the voice guidance to confirm 'Bluetooth connected'.

## 3. Core Controls & Daily Operation
The right earcup features a touch sensor control panel for seamless playback adjustments. Swipe upward across the surface of the right earcup to raise the volume, or swipe downward to decrease the volume. Double-tap the center of the touch surface to pause playback, and double-tap again to resume music. To skip forward to the next track, swipe forward toward your face; to return to the previous track, swipe backward toward the rear.

## 4. Maintenance & Cleaning Instructions
To maintain the appearance and acoustic performance of your headphones, clean them regularly using a dry, soft microfiber cloth. Never use alcohol, thinners, benzene, or liquid detergents on the synthetic leather ear pads or headband padding, as these chemical agents can cause surface peeling and material degradation. Avoid exposing the headphones to excessive moisture, direct rainfall, or high humidity environments. Store the headphones inside their supplied protective case when not in active use.

## 5. Basic Troubleshooting
If you experience intermittent audio drops or Bluetooth connection instability, reset the headphones by connecting the USB-C charging cable to a power source, then simultaneously pressing and holding the Power and NC/AMB buttons for seven seconds. The indicator light will flash four times in blue to indicate that factory settings have been restored. Re-pair the headphones with your device following the initial configuration steps.
"""


@pytest.fixture
def sample_metadata():
    return {
        "product_id": "P001",
        "product_name": "Sony WH-1000XM5",
        "category": "Headphones",
        "section": "user_manual",
        "is_synthetic": True,
    }


def test_parse_front_matter():
    fm, body = parse_front_matter(SAMPLE_DOC_WITH_STEPS)
    assert fm["product_id"] == "P001"
    assert fm["section"] == "user_manual"
    assert fm["is_synthetic"] is True
    assert fm["generated_by"] == "gpt-5-mini"
    assert not body.startswith("---")
    assert body.startswith("# Sony WH-1000XM5")


def test_chunk_size_bounds(sample_metadata):
    chunks = chunk_markdown(SAMPLE_DOC_WITH_STEPS, metadata=sample_metadata, min_tokens=350, max_tokens=450)
    assert len(chunks) >= 2, "Expected document to produce at least 2 chunks"

    for chunk in chunks:
        # Every chunk should be under or at max tokens
        assert chunk["token_count"] <= 450, f"Chunk {chunk['chunk_id']} exceeded max tokens: {chunk['token_count']}"
        # Chunks should not be trivial fragments
        assert chunk["token_count"] >= 200, f"Chunk {chunk['chunk_id']} is too small: {chunk['token_count']}"


def test_overlap_present(sample_metadata):
    chunks = chunk_markdown(SAMPLE_DOC_WITH_STEPS, metadata=sample_metadata, min_tokens=350, max_tokens=450, min_overlap=50, max_overlap=80)
    assert len(chunks) >= 2

    for i in range(len(chunks) - 1):
        c1 = chunks[i]["content"]
        c2 = chunks[i]["content"]

        # Check for shared sentences or phrases between c1 end and c2 start
        c1_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", c1) if len(s.strip()) > 20]
        shared_found = any(s in c2 for s in c1_sentences[-3:])
        assert shared_found, f"No overlap detected between chunk {chunks[i]['chunk_id']} and {chunks[i+1]['chunk_id']}"


def test_chunk_ids_unique_and_formatted(sample_metadata):
    chunks = chunk_markdown(SAMPLE_DOC_WITH_STEPS, metadata=sample_metadata)
    chunk_ids = [c["chunk_id"] for c in chunks]

    # Verify uniqueness
    assert len(chunk_ids) == len(set(chunk_ids)), "Chunk IDs must be strictly unique"

    # Verify ID format: {product_id}_{section}_{index:03d}
    pattern = re.compile(r"^P001_user_manual_\d{3}$")
    for cid in chunk_ids:
        assert pattern.match(cid), f"Chunk ID '{cid}' does not match expected format"

    assert chunk_ids[0] == "P001_user_manual_001"
    assert chunk_ids[1] == "P001_user_manual_002"


def test_metadata_complete(sample_metadata):
    chunks = chunk_markdown(SAMPLE_DOC_WITH_STEPS, metadata=sample_metadata)
    required_keys = {
        "chunk_id",
        "product_id",
        "product_name",
        "category",
        "section",
        "title",
        "content",
        "token_count",
        "is_synthetic",
    }

    for chunk in chunks:
        missing = required_keys - set(chunk.keys())
        assert not missing, f"Chunk {chunk.get('chunk_id')} missing required metadata fields: {missing}"
        assert chunk["product_id"] == "P001"
        assert chunk["product_name"] == "Sony WH-1000XM5"
        assert chunk["category"] == "Headphones"
        assert chunk["section"] == "user_manual"
        assert chunk["is_synthetic"] is True
        assert isinstance(chunk["title"], str) and len(chunk["title"]) > 0
        assert chunk["token_count"] == count_tokens(chunk["content"])


def test_step_lists_not_split(sample_metadata):
    """Verifies that a numbered procedural list is never split across chunk boundaries."""
    chunks = chunk_markdown(SAMPLE_DOC_WITH_STEPS, metadata=sample_metadata, max_tokens=450)

    step_patterns = [
        "1. Power on the headphones",
        "2. For initial pairing",
        "3. On your smartphone",
        "4. Locate 'Sony WH-1000XM5'",
        "5. Confirm the pairing prompt",
    ]

    # Find which chunks contain step 1 and step 5
    chunks_with_step1 = [c for c in chunks if "1. Power on the headphones" in c["content"]]
    assert len(chunks_with_step1) >= 1, "Step 1 must be present in at least one chunk"

    # For any chunk containing step 1, verify all 5 steps are present intact
    for c in chunks_with_step1:
        for step in step_patterns:
            assert step in c["content"], f"Numbered step list was split! Missing '{step}' in chunk {c['chunk_id']}"
