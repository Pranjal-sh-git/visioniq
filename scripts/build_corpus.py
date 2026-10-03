"""Corpus Generation Script for VisionIQ RAG.

Reads data/products/products.json and generates 4 structured markdown documents
for each product under data/corpus/<product_id>/:
  - user_manual.md
  - faq.md
  - warranty.md
  - usage_guide.md

Follows docs/rag_design.md:
  - Uses gpt-5-mini via existing llm service ONLY as a writer
  - Strictly enforces: factual claims about specs/features must come ONLY from products.json
  - Procedural content (setup, troubleshooting, warranty terms) is generic and plausible
  - Adds standard YAML front matter (product_id, section, is_synthetic: true, generated_by, generated_at)
  - Target size: ~400-900 tokens with ## section headers
  - Logs total tokens used across all generations
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import re
import sys
import threading
import time

# Ensure project root and backend are on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

import tiktoken
from services.llm import get_azure_openai_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("visioniq.build_corpus")

enc = tiktoken.get_encoding("cl100k_base")

SECTIONS = ["user_manual", "faq", "warranty", "usage_guide"]

SECTION_PROMPTS = {
    "user_manual": """Write an official user manual for this product.
Include:
## 1. Product Overview & In the Box
## 2. Setup & Initial Configuration (include numbered procedural steps 1., 2., 3.)
## 3. Core Controls & Daily Operation
## 4. Maintenance & Cleaning Instructions
## 5. Basic Troubleshooting""",

    "faq": """Write a comprehensive Frequently Asked Questions (FAQ) guide for this product.
Include 5 to 7 detailed Q&A pairs formatted under ## section headers:
## Q: ...
A: ...
Cover connectivity/compatibility, battery/power/fit, maintenance, daily usage nuances, and common questions.""",

    "warranty": """Write an authoritative Warranty and Customer Support policy document for this product.
Include:
## 1. Warranty Coverage & Duration
## 2. What Is Covered
## 3. What Is Excluded (Misuse, wear & tear, unauthorized modifications)
## 4. How to File a Warranty Claim (include numbered procedural steps 1., 2., 3.)
## 5. Customer Support & Service Channels""",

    "usage_guide": """Write a comprehensive Usage and Best Practices guide for this product.
Include:
## 1. Ergonomics & Ideal Fit / Placement
## 2. Optimal Performance & Environmental Recommendations
## 3. Best Practices for Product Longevity
## 4. Recommended Use Cases & Scenarios
## 5. Do's and Don'ts for Daily Use"""
}


def build_system_and_user_prompt(product: dict, section: str) -> tuple[str, str]:
    specs_formatted = json.dumps(product.get("specifications", {}), indent=2)
    features_formatted = json.dumps(product.get("features", []), indent=2)
    
    system_prompt = (
        "You are an expert technical documentation writer for consumer products.\n"
        "Your task is to write clean, authentic, highly structured markdown documentation.\n\n"
        "CRITICAL FACTUAL AND SPECIFICATION RULES:\n"
        "1. Every factual claim about specifications, technical details, materials, or features "
        "must come STRICTLY from the provided product JSON.\n"
        "2. DO NOT invent new numeric specs (battery hours, weight, driver sizes, dimensions, "
        "impedance, voltages, mAh, etc.) beyond what is explicitly listed in the JSON.\n"
        "3. If a specification is not mentioned in the JSON, do NOT make up a number for it; "
        "refer to the listed specs or provide general procedural guidance.\n"
        "4. Procedural content (step-by-step setup, pairing, maintenance, troubleshooting trees, "
        "and standard warranty terms) should be generic, realistic, and plausible for this category of product.\n"
        "5. Target length: 450 to 700 words (approximately 500 to 850 tokens). Each section must have ## headers.\n"
        "6. Output ONLY the markdown document starting with '# {Product Name} - {Doc Type}'. "
        "Do NOT output YAML front matter or backtick code fences around the entire markdown output."
    )

    section_guidance = SECTION_PROMPTS.get(section, "")
    user_prompt = f"""Write the '{section}.md' documentation for the following product:

Product ID: {product['id']}
Product Name: {product['name']}
Brand: {product['brand']}
Category: {product['category']}
Description: {product['description']}
Specifications:
{specs_formatted}
Features:
{features_formatted}

Document Guidance:
{section_guidance}

Remember:
- Use ## for all main section headers.
- Strictly adhere to the numbers and specifications in the JSON without inventing new numerical specs.
- Do NOT output YAML front matter (it will be added programmatically).
- Start directly with '# {product['name']} - {section.replace('_', ' ').title()}'."""

    return system_prompt, user_prompt


def generate_single_document(
    client,
    product: dict,
    section: str,
    output_path: Path,
    force: bool = False
) -> dict:
    if output_path.exists() and not force:
        try:
            content = output_path.read_text(encoding="utf-8")
            # compute tokens of content without front matter
            body = re.sub(r"^---[\s\S]*?---\n*", "", content)
            token_count = len(enc.encode(body))
            if 350 <= token_count <= 1200:
                logger.info(f"Skipping existing {product['id']}/{section}.md ({token_count} tokens)")
                return {
                    "product_id": product["id"],
                    "section": section,
                    "status": "cached",
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "body_tokens": token_count,
                }
        except Exception:
            pass

    sys_prompt, user_prompt = build_system_and_user_prompt(product, section)
    
    for attempt in range(3):
        try:
            res = client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_completion_tokens=4500,
            )
            raw_content = res.choices[0].message.content or ""
            # Strip enclosing code fences if any
            clean_body = raw_content.strip()
            if clean_body.startswith("```markdown"):
                clean_body = clean_body[len("```markdown"):].strip()
            elif clean_body.startswith("```"):
                clean_body = clean_body[3:].strip()
            if clean_body.endswith("```"):
                clean_body = clean_body[:-3].strip()

            # Ensure any stray YAML front matter from model is stripped
            clean_body = re.sub(r"^---[\s\S]*?---\n*", "", clean_body).strip()

            body_tokens = len(enc.encode(clean_body))
            if body_tokens < 350:
                raise ValueError(f"Generated text too short ({body_tokens} tokens), retrying...")

            # Construct standardized YAML front matter
            now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            front_matter = (
                "---\n"
                f"product_id: {product['id']}\n"
                f"section: {section}\n"
                "is_synthetic: true\n"
                "generated_by: gpt-5-mini\n"
                f"generated_at: '{now_iso}'\n"
                "---\n\n"
            )
            full_content = front_matter + clean_body + "\n"

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(full_content, encoding="utf-8")

            body_tokens = len(enc.encode(clean_body))
            usage = res.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            total_tokens = usage.total_tokens if usage else 0

            logger.info(
                f"Generated {product['id']}/{section}.md: {body_tokens} body tokens "
                f"(LLM used {total_tokens} total tokens)"
            )
            return {
                "product_id": product["id"],
                "section": section,
                "status": "generated",
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "body_tokens": body_tokens,
            }
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed for {product['id']}/{section}: {e}")
            time.sleep(2 * (attempt + 1))

    raise RuntimeError(f"Failed to generate {product['id']}/{section}.md after 3 attempts")


def main():
    parser = argparse.ArgumentParser(description="Generate VisionIQ RAG corpus documents")
    parser.add_argument("--products", default="data/products/products.json", help="Path to products.json")
    parser.add_argument("--output-dir", default="data/corpus", help="Output corpus directory")
    parser.add_argument("--workers", type=int, default=8, help="Parallel worker threads")
    parser.add_argument("--force", action="store_true", help="Force regenerate existing docs")
    args = parser.parse_args()

    products_path = PROJECT_ROOT / args.products
    corpus_dir = PROJECT_ROOT / args.output_dir
    corpus_dir.mkdir(parents=True, exist_ok=True)

    with open(products_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    logger.info(f"Loaded {len(products)} products from {products_path}")
    logger.info(f"Target: {len(products) * len(SECTIONS)} total documents in {corpus_dir}")

    client = get_azure_openai_client()

    tasks = []
    for product in products:
        p_id = product["id"]
        prod_dir = corpus_dir / p_id
        for sec in SECTIONS:
            doc_path = prod_dir / f"{sec}.md"
            tasks.append((product, sec, doc_path))

    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens_used = 0
    generated_count = 0
    cached_count = 0
    body_tokens_list = []

    lock = threading.Lock()
    start_time = time.perf_counter()

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_task = {
            executor.submit(generate_single_document, client, prod, sec, path, args.force): (prod["id"], sec)
            for prod, sec, path in tasks
        }

        for future in as_completed(future_to_task):
            p_id, sec = future_to_task[future]
            try:
                res = future.result()
                with lock:
                    if res["status"] == "generated":
                        generated_count += 1
                        total_prompt_tokens += res["prompt_tokens"]
                        total_completion_tokens += res["completion_tokens"]
                        total_tokens_used += res["total_tokens"]
                    else:
                        cached_count += 1
                    body_tokens_list.append(res["body_tokens"])
            except Exception as e:
                logger.error(f"Failed task for {p_id}/{sec}: {e}")
                raise

    elapsed = time.perf_counter() - start_time
    logger.info("=" * 70)
    logger.info("VisionIQ Corpus Generation Complete!")
    logger.info(f"Total documents: {len(tasks)} (Generated: {generated_count}, Cached: {cached_count})")
    logger.info(f"Total Time: {elapsed:.2f}s (Average: {elapsed / max(1, generated_count):.2f}s per generated doc)")
    logger.info(f"Total LLM Tokens Used: {total_tokens_used:,} "
                f"(Prompt: {total_prompt_tokens:,}, Completion: {total_completion_tokens:,})")
    if body_tokens_list:
        min_tok = min(body_tokens_list)
        max_tok = max(body_tokens_list)
        avg_tok = sum(body_tokens_list) / len(body_tokens_list)
        logger.info(f"Document Body Tokens: Min={min_tok}, Avg={avg_tok:.1f}, Max={max_tok}")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
