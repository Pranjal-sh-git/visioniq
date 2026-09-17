"""Direct RAG specification answer extraction for P001."""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from services.rag.rag_service import answer_product_question

questions = [
    "What is its battery life?",
    "What is its weight?",
    "What is the connectivity type?",
    "What is the driver size?",
    "How is it charged?",
]

print("\n" + "=" * 70)
print("CATALOG GROUNDED SPECIFICATION ANSWERS FOR P001")
print("=" * 70)

for q in questions:
    res = answer_product_question("P001", q)
    print(f"Q: {q}")
    print(f"   -> Grounded Field : {res.get('grounded_field')}")
    print(f"   -> Catalog Value  : {res.get('catalog_value')}")
    print(f"   -> Answer         : {res.get('answer')}")
    print()

print("=" * 70)
