"""One-time offline model downloader for VisionIQ.

Downloads CLIP ViT-B/32, all-MiniLM-L6-v2, and openai/whisper-tiny into the local
Hugging Face cache directory. Run this once on fresh machines before starting the server.
"""

import sys
import time
from pathlib import Path

# Add project root and backend to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))


def download_models():
    print("=" * 70)
    print("VisionIQ: Downloading ML Models to Local Hugging Face Cache")
    print("=" * 70)

    # 1. CLIP ViT-B/32
    print("\n[1/3] Downloading CLIP ViT-B/32 (sentence-transformers/clip-ViT-B-32)...")
    t0 = time.perf_counter()
    from sentence_transformers import SentenceTransformer
    SentenceTransformer("clip-ViT-B-32")
    print(f"  -> CLIP ViT-B/32 cached successfully in {time.perf_counter() - t0:.2f}s.")

    # 2. all-MiniLM-L6-v2
    print("\n[2/3] Downloading all-MiniLM-L6-v2 (sentence-transformers/all-MiniLM-L6-v2)...")
    t0 = time.perf_counter()
    SentenceTransformer("all-MiniLM-L6-v2")
    print(f"  -> all-MiniLM-L6-v2 cached successfully in {time.perf_counter() - t0:.2f}s.")

    # 3. Whisper Tiny (openai/whisper-tiny)
    print("\n[3/3] Downloading Whisper Tiny (openai/whisper-tiny)...")
    t0 = time.perf_counter()
    from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
    AutoModelForSpeechSeq2Seq.from_pretrained("openai/whisper-tiny")
    AutoProcessor.from_pretrained("openai/whisper-tiny")
    print(f"  -> openai/whisper-tiny cached successfully in {time.perf_counter() - t0:.2f}s.")

    print("\n" + "=" * 70)
    print("All models successfully cached in Hugging Face cache!")
    print("You can now start the VisionIQ server with local_files_only enabled.")
    print("=" * 70)


if __name__ == "__main__":
    download_models()
