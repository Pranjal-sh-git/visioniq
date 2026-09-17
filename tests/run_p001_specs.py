"""Multi-question grounding test across catalog specifications for P001."""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from agent.agent import VisionIQAgent

def run_spec_questions():
    agent = VisionIQAgent()
    questions = [
        "What is its battery life?",
        "What is its weight?",
        "What is the connectivity type?",
        "What is the driver size?",
        "How is it charged?",
    ]

    print("\n" + "=" * 70)
    print("GROUNDED SPECIFICATION Q&A FOR P001 (Sony WH-1000XM5)")
    print("=" * 70)

    for q in questions:
        try:
            res = agent.run(q, product_id="P001")
            ans = res["tool_output"].get("answer") if isinstance(res.get("tool_output"), dict) else res.get("tool_output")
            print(f"{q} -> {ans}")
        except Exception as e:
            print(f"{q} -> ERROR: {e}")

    print("=" * 70)


if __name__ == "__main__":
    run_spec_questions()
