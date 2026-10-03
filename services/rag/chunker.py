"""Markdown Header-Aware Recursive Chunker for VisionIQ RAG.

Splits technical markdown documents into overlapping chunks honoring markdown
headers, token boundaries (350-450 tokens using tiktoken cl100k_base), and overlap
(50-80 tokens). Preserves procedural numbered step lists as atomic units when they fit under max tokens.

Follows docs/rag_design.md:
  - Target size: 350 - 450 tokens
  - Overlap: 50 - 80 tokens
  - Numbered lists are never split internally if total list size <= max_tokens
  - Deterministic chunk_id: {product_id}_{section}_{index:03d}
  - Complete metadata: product_id, product_name, category, section, title, token_count, is_synthetic
"""

import re
from typing import Any, Dict, List, Optional
import tiktoken

enc = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Counts cl100k_base tokens for a given string."""
    return len(enc.encode(text))


def parse_front_matter(text: str) -> tuple[Dict[str, Any], str]:
    """Parses and strips YAML front matter from markdown text."""
    front_matter: Dict[str, Any] = {}
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            raw_fm = parts[1]
            for line in raw_fm.splitlines():
                if ":" in line:
                    key, val = line.split(":", 1)
                    clean_val = val.strip().strip("'\"")
                    if clean_val.lower() == "true":
                        front_matter[key.strip()] = True
                    elif clean_val.lower() == "false":
                        front_matter[key.strip()] = False
                    else:
                        front_matter[key.strip()] = clean_val
            body = parts[2].strip()
            return front_matter, body
    return front_matter, text.strip()


def is_numbered_step_line(line: str) -> bool:
    """Returns True if the line starts with a numbered step like '1. ', '2) '."""
    return bool(re.match(r"^\s*\d+[\.\)]\s+", line))


def is_bullet_line(line: str) -> bool:
    """Returns True if line starts with a bullet point."""
    return bool(re.match(r"^\s*[\-\*\+]\s+", line))


def split_into_atomic_blocks(section_text: str, max_tokens: int = 450) -> List[Dict[str, Any]]:
    """Breaks section body into atomic structural blocks (paragraphs, numbered lists, tables).

    Numbered step lists are kept as single atomic blocks when their total tokens <= max_tokens.
    """
    raw_paragraphs = re.split(r"\n\s*\n", section_text.strip())
    blocks: List[Dict[str, Any]] = []

    for para in raw_paragraphs:
        clean_para = para.strip()
        if not clean_para:
            continue

        lines = clean_para.splitlines()
        first_line = lines[0].strip()

        # 1. Numbered step list detection
        if is_numbered_step_line(first_line):
            # Check if all or most lines are numbered steps
            is_step_list = True
            token_size = count_tokens(clean_para)
            if token_size <= max_tokens:
                blocks.append({
                    "type": "numbered_list",
                    "text": clean_para,
                    "tokens": token_size,
                    "atomic": True,
                })
                continue

        # 2. Large paragraph splitting (if a single prose paragraph > max_tokens)
        para_tokens = count_tokens(clean_para)
        if para_tokens > max_tokens:
            # Split by sentences
            sentences = re.split(r"(?<=[.!?])\s+", clean_para)
            curr_sent_block = []
            curr_sent_tokens = 0
            for sent in sentences:
                s_tok = count_tokens(sent)
                if curr_sent_tokens + s_tok > max_tokens and curr_sent_block:
                    joined = " ".join(curr_sent_block)
                    blocks.append({
                        "type": "paragraph_part",
                        "text": joined,
                        "tokens": count_tokens(joined),
                        "atomic": False,
                    })
                    curr_sent_block = [sent]
                    curr_sent_tokens = s_tok
                else:
                    curr_sent_block.append(sent)
                    curr_sent_tokens += s_tok
            if curr_sent_block:
                joined = " ".join(curr_sent_block)
                blocks.append({
                    "type": "paragraph_part",
                    "text": joined,
                    "tokens": count_tokens(joined),
                    "atomic": False,
                })
        else:
            blocks.append({
                "type": "paragraph",
                "text": clean_para,
                "tokens": para_tokens,
                "atomic": False,
            })

    return blocks


def parse_markdown_sections(markdown_text: str) -> List[Dict[str, Any]]:
    """Splits markdown into hierarchical sections based on #, ##, ### headers."""
    lines = markdown_text.splitlines()
    sections: List[Dict[str, Any]] = []
    
    current_header = ""
    current_title = "Overview"
    current_lines: List[str] = []

    for line in lines:
        header_match = re.match(r"^(#{1,4})\s+(.+)$", line.strip())
        if header_match:
            # Save previous section if it has content
            if current_lines:
                sec_text = "\n".join(current_lines).strip()
                if sec_text:
                    sections.append({
                        "header": current_header,
                        "title": current_title,
                        "text": sec_text,
                    })
                current_lines = []
            current_header = line.strip()
            # Clean title (remove leading numbers like '1. ', '## ')
            raw_title = header_match.group(2).strip()
            cleaned_title = re.sub(r"^(?:Q\d+[:\.]|\d+[\.\)])\s*", "", raw_title).strip()
            current_title = cleaned_title if cleaned_title else raw_title
        else:
            current_lines.append(line)

    if current_lines:
        sec_text = "\n".join(current_lines).strip()
        if sec_text:
            sections.append({
                "header": current_header,
                "title": current_title,
                "text": sec_text,
            })

    return sections


def extract_overlap_text(chunk_text: str, target_min: int = 50, target_max: int = 80) -> str:
    """Extracts trailing sentences or non-atomic content for overlap (50-80 tokens).

    Never slices into the middle of a numbered step list.
    """
    paragraphs = re.split(r"\n\s*\n", chunk_text.strip())
    if not paragraphs:
        return ""

    # Check last paragraph
    last_para = paragraphs[-1].strip()
    if is_numbered_step_line(last_para):
        last_tokens = count_tokens(last_para)
        # If the whole numbered list is within overlap range, we can take it
        if target_min <= last_tokens <= target_max:
            return last_para
        # Otherwise, do NOT cut inside the step list; look at preceding paragraph if exists
        if len(paragraphs) > 1:
            prev_para = paragraphs[-2].strip()
            if not is_numbered_step_line(prev_para):
                sentences = re.split(r"(?<=[.!?])\s+", prev_para)
                accum = []
                for s in reversed(sentences):
                    accum.insert(0, s)
                    tok = count_tokens(" ".join(accum))
                    if tok >= target_min:
                        break
                joined = " ".join(accum)
                if count_tokens(joined) <= target_max + 10:
                    return joined
        return ""

    # Regular prose paragraph: take last 1-2 sentences
    sentences = re.split(r"(?<=[.!?])\s+", last_para)
    accum = []
    for s in reversed(sentences):
        accum.insert(0, s)
        tok = count_tokens(" ".join(accum))
        if tok >= target_min:
            break

    overlap = " ".join(accum)
    overlap_tokens = count_tokens(overlap)
    if overlap_tokens > target_max + 15:
        # trim if too large
        accum = accum[-1:]
        overlap = " ".join(accum)

    return overlap


def chunk_markdown(
    markdown_text: str,
    metadata: Optional[Dict[str, Any]] = None,
    min_tokens: int = 350,
    max_tokens: int = 450,
    min_overlap: int = 50,
    max_overlap: int = 80,
) -> List[Dict[str, Any]]:
    """Chunks markdown document into header-aware overlapping chunks.

    Args:
        markdown_text: Raw markdown content (with or without front matter).
        metadata: Product metadata dict (product_id, product_name, category, section).
        min_tokens: Minimum target token size per chunk (default 350).
        max_tokens: Maximum target token size per chunk (default 450).
        min_overlap: Minimum overlap tokens between consecutive chunks (default 50).
        max_overlap: Maximum overlap tokens between consecutive chunks (default 80).

    Returns:
        List of chunk dicts matching VisionIQ RAG schema.
    """
    if metadata is None:
        metadata = {}

    front_matter, body = parse_front_matter(markdown_text)
    product_id = metadata.get("product_id") or front_matter.get("product_id", "UNKNOWN")
    section = metadata.get("section") or front_matter.get("section", "doc")
    product_name = metadata.get("product_name") or front_matter.get("product_name", product_id)
    category = metadata.get("category") or front_matter.get("category", "General")
    is_synthetic = metadata.get("is_synthetic", front_matter.get("is_synthetic", True))

    total_body_tokens = count_tokens(body)
    if total_body_tokens == 0:
        return []

    # If the entire document fits under max_tokens, return it as a single chunk
    if total_body_tokens <= max_tokens:
        first_title = "Overview"
        header_match = re.search(r"^#{1,4}\s+(.+)$", body, re.MULTILINE)
        if header_match:
            first_title = re.sub(r"^(?:Q\d+[:\.]|\d+[\.\)])\s*", "", header_match.group(1)).strip()

        return [{
            "chunk_id": f"{product_id}_{section}_001",
            "product_id": product_id,
            "product_name": product_name,
            "category": category,
            "section": section,
            "title": first_title,
            "content": body,
            "token_count": total_body_tokens,
            "is_synthetic": is_synthetic,
        }]

    # Parse document into sections and atomic blocks
    sections = parse_markdown_sections(body)
    all_elements: List[Dict[str, Any]] = []

    for sec in sections:
        sec_title = sec["title"]
        sec_header = sec["header"]
        sec_blocks = split_into_atomic_blocks(sec["text"], max_tokens=max_tokens)
        
        # Prepend header to first block if not already present
        if sec_blocks and sec_header:
            if not sec_blocks[0]["text"].startswith("#"):
                sec_blocks[0]["text"] = f"{sec_header}\n\n{sec_blocks[0]['text']}"
                sec_blocks[0]["tokens"] = count_tokens(sec_blocks[0]["text"])

        for b in sec_blocks:
            b["title"] = sec_title
            all_elements.append(b)

    chunks: List[Dict[str, Any]] = []
    current_blocks: List[Dict[str, Any]] = []
    current_tokens = 0
    current_title = sections[0]["title"] if sections else "Overview"
    overlap_prefix = ""

    for elem in all_elements:
        elem_tokens = elem["tokens"]
        new_total = current_tokens + elem_tokens

        if new_total <= max_tokens:
            current_blocks.append(elem)
            current_tokens = new_total
            if elem.get("title"):
                current_title = elem["title"]
        else:
            # Current chunk has enough content
            if current_blocks:
                chunk_body = "\n\n".join(b["text"] for b in current_blocks).strip()
                if overlap_prefix and not chunk_body.startswith(overlap_prefix):
                    chunk_body = f"{overlap_prefix}\n\n{chunk_body}".strip()

                chunk_tok = count_tokens(chunk_body)
                chunks.append({
                    "title": current_title,
                    "content": chunk_body,
                    "token_count": chunk_tok,
                })

                # Compute overlap for the next chunk
                overlap_prefix = extract_overlap_text(chunk_body, target_min=min_overlap, target_max=max_overlap)
                overlap_tokens = count_tokens(overlap_prefix) if overlap_prefix else 0

                current_blocks = [elem]
                current_tokens = elem_tokens + overlap_tokens
                if elem.get("title"):
                    current_title = elem["title"]
            else:
                # Element alone is large
                current_blocks = [elem]
                current_tokens = elem_tokens

    # Finalize last chunk
    if current_blocks:
        trailing_text = "\n\n".join(b["text"] for b in current_blocks).strip()
        trailing_tokens = count_tokens(trailing_text)

        # 1. If trailing text fits into the previous chunk without exceeding max_tokens, merge it
        if chunks and (chunks[-1]["token_count"] + trailing_tokens <= max_tokens):
            merged_body = f"{chunks[-1]['content']}\n\n{trailing_text}".strip()
            chunks[-1]["content"] = merged_body
            chunks[-1]["token_count"] = count_tokens(merged_body)
        else:
            chunk_body = trailing_text
            if overlap_prefix and not chunk_body.startswith(overlap_prefix):
                chunk_body = f"{overlap_prefix}\n\n{chunk_body}".strip()

            chunk_tok = count_tokens(chunk_body)

            # 2. If final chunk is under min_tokens and we have a previous chunk,
            # pull trailing context from previous chunk so the final chunk reaches ~350 tokens
            if chunk_tok < min_tokens and chunks:
                prev_content = chunks[-1]["content"]
                # Try pulling enough tokens from previous chunk
                needed_tokens = min_tokens - chunk_tok + 20
                prev_sentences = re.split(r"(?<=[.!?])\s+", prev_content)
                pulled = []
                for s in reversed(prev_sentences):
                    pulled.insert(0, s)
                    if count_tokens(" ".join(pulled)) >= needed_tokens:
                        break
                overlap_candidate = " ".join(pulled)
                if overlap_candidate and overlap_candidate not in chunk_body:
                    extended_body = f"{overlap_candidate}\n\n{chunk_body}".strip()
                    extended_tok = count_tokens(extended_body)
                    if extended_tok <= max_tokens:
                        chunk_body = extended_body
                        chunk_tok = extended_tok

            chunks.append({
                "title": current_title,
                "content": chunk_body,
                "token_count": chunk_tok,
            })

    # Build final formatted list with deterministic chunk_ids
    result = []
    for idx, c in enumerate(chunks, start=1):
        result.append({
            "chunk_id": f"{product_id}_{section}_{idx:03d}",
            "product_id": product_id,
            "product_name": product_name,
            "category": category,
            "section": section,
            "title": c["title"],
            "content": c["content"],
            "token_count": c["token_count"],
            "is_synthetic": is_synthetic,
        })

    return result
