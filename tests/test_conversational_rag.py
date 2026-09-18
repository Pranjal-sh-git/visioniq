import sys
import os
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
from services.rag.rag_service import answer_product_question

test_cases = [
    (
        "P001",
        "Is this headphone good for frequent flyers and how long does the battery last with noise cancelling on?"
    ),
    (
        "P001",
        "What colors is it available in, and how much does it weigh?"
    ),
    (
        "P010",
        "I suffer from lower back pain during long working hours. How does this chair support posture?"
    ),
    (
        "P015",
        "Can I use these shoes for road running and what is the heel drop?"
    ),
    (
        "P001",
        "Does it have an IPX7 waterproof rating for swimming?"
    )
]

def main():
    print("================================================================================")
    print("          VISIONIQ CONVERSATIONAL RAG & FOUNDRY AGENT EVALUATION TEST          ")
    print("================================================================================\n")

    for pid, query in test_cases:
        print(f"[*] Product ID: {pid}")
        print(f"[?] User Question: '{query}'")
        res = answer_product_question(pid, query)
        print(f"[+] Grounded Answer:\n    {res.get('answer')}")
        print(f"[i] Metadata: is_grounded={res.get('is_grounded')}, source_count={len(res.get('sources', []))}")
        print("-" * 80 + "\n")

if __name__ == "__main__":
    main()
