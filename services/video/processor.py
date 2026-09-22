"""Video Processing and Temporal Intelligence Service.

Accepts video files, extracts audio, transcribes with timestamps, extracts
keyframes at ~10s intervals, creates semantic topic chunks with embeddings,
and caches results to disk keyed by video_id to prevent redundant processing.
"""

import hashlib
import json
import logging
import os
from pathlib import Path
import sys
from typing import Any, Optional, Union
import av
import cv2
import numpy as np
from PIL import Image

# Ensure workspace root and backend are on sys.path
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent.parent
for directory in (str(ROOT_DIR), str(ROOT_DIR / "backend")):
    if directory not in sys.path:
        sys.path.insert(0, directory)

try:
    from backend.config import settings
except ImportError:
    from config import settings

from services.video.embeddings import generate_transcript_embedding

logger = logging.getLogger(__name__)

CACHE_DIR = ROOT_DIR / "data" / "cache" / "video_analysis"
KEYFRAMES_DIR = CACHE_DIR / "keyframes"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
KEYFRAMES_DIR.mkdir(parents=True, exist_ok=True)

_ASR_PIPELINE = None


def get_asr_pipeline():
    """Lazy-loads Whisper Automatic Speech Recognition pipeline."""
    global _ASR_PIPELINE
    if _ASR_PIPELINE is None:
        try:
            from transformers import pipeline
            logger.info("Loading Whisper ASR model (openai/whisper-tiny)...")
            _ASR_PIPELINE = pipeline(
                "automatic-speech-recognition",
                model="openai/whisper-tiny",
                chunk_length_s=30,
                return_timestamps=True,
            )
        except Exception as e:
            logger.warning(f"Whisper ASR pipeline could not be loaded: {e}")
            _ASR_PIPELINE = None
    return _ASR_PIPELINE


def compute_video_id(file_path: Union[str, Path], file_bytes: Optional[bytes] = None) -> str:
    """Computes a deterministic SHA256 video_id from file contents."""
    hasher = hashlib.sha256()
    if file_bytes:
        hasher.update(file_bytes)
    else:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
    return f"vid_{hasher.hexdigest()[:16]}"


def extract_audio_array(video_path: Union[str, Path]) -> Optional[tuple[np.ndarray, int]]:
    """Extracts raw audio from a video file into a 16kHz mono float32 numpy array.

    Args:
        video_path: Path to the video file.

    Returns:
        tuple[np.ndarray, int]: (audio_samples, sample_rate) or None if no audio track.
    """
    try:
        container = av.open(str(video_path))
        audio_stream = next((s for s in container.streams if s.type == "audio"), None)
        if audio_stream is None:
            logger.info("No audio stream found in video container.")
            return None

        # Resample to 16000Hz mono for Whisper ASR
        resampler = av.AudioResampler(format="fltp", layout="mono", rate=16000)
        audio_frames = []

        for packet in container.demux(audio_stream):
            for frame in packet.decode():
                resampled_frames = resampler.resample(frame)
                for rf in resampled_frames:
                    audio_frames.append(rf.to_ndarray())

        if not audio_frames:
            return None

        audio_data = np.concatenate(audio_frames, axis=1).squeeze()
        return audio_data.astype(np.float32), 16000
    except Exception as e:
        logger.warning(f"Audio extraction failed for {video_path}: {e}")
        return None


def extract_keyframes(
    video_path: Union[str, Path],
    video_id: str,
    interval_sec: float = 10.0,
) -> list[dict[str, Any]]:
    """Extracts keyframes at ~interval_sec seconds and saves them to cache.

    Args:
        video_path: Path to video file.
        video_id: Unique video identifier.
        interval_sec: Interval in seconds between extracted frames (default: 10s).

    Returns:
        list[dict[str, Any]]: List of keyframe metadata dictionaries.
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / fps if fps > 0 else 0.0

    frame_interval = int(round(fps * interval_sec))
    if frame_interval <= 0:
        frame_interval = 1

    keyframes_folder = KEYFRAMES_DIR / video_id
    keyframes_folder.mkdir(parents=True, exist_ok=True)

    keyframes = []
    current_frame = 0
    keyframe_index = 0

    while current_frame < total_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
        ret, frame = cap.read()
        if not ret:
            break

        timestamp_sec = round(current_frame / fps, 2)
        keyframe_filename = f"keyframe_{keyframe_index:04d}_{int(timestamp_sec)}s.jpg"
        keyframe_path = keyframes_folder / keyframe_filename

        # Convert BGR (cv2) to RGB (PIL) and save as JPEG
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_frame)
        pil_img.save(keyframe_path, "JPEG", quality=85)

        keyframes.append({
            "keyframe_index": keyframe_index,
            "timestamp_sec": timestamp_sec,
            "image_filename": keyframe_filename,
            "image_path": str(keyframe_path),
        })

        keyframe_index += 1
        current_frame += frame_interval

    cap.release()
    return keyframes


def transcribe_audio(video_path: Union[str, Path]) -> list[dict[str, Any]]:
    """Transcribes audio with timestamped segments using Whisper."""
    audio_info = extract_audio_array(video_path)
    if audio_info is None:
        return []

    audio_array, sample_rate = audio_info
    asr = get_asr_pipeline()
    if asr is None:
        logger.warning("ASR pipeline unavailable; skipping transcription.")
        return []

    try:
        result = asr({"raw": audio_array, "sampling_rate": sample_rate})
        raw_chunks = result.get("chunks", [])

        segments = []
        if raw_chunks:
            for c in raw_chunks:
                ts = c.get("timestamp", (0.0, 0.0))
                start_t = float(ts[0]) if ts[0] is not None else 0.0
                end_t = float(ts[1]) if ts[1] is not None else start_t + 5.0
                text = c.get("text", "").strip()
                if text:
                    segments.append({
                        "start_time": round(start_t, 2),
                        "end_time": round(end_t, 2),
                        "text": text,
                    })
        elif result.get("text"):
            segments.append({
                "start_time": 0.0,
                "end_time": 10.0,
                "text": result.get("text", "").strip(),
            })

        return segments
    except Exception as e:
        logger.warning(f"Transcription error: {e}")
        return []


def create_timestamped_chunks(
    video_id: str,
    segments: list[dict[str, Any]],
    keyframes: list[dict[str, Any]],
    duration_sec: float,
    chunk_window_sec: float = 20.0,
) -> list[dict[str, Any]]:
    """Creates timestamped semantic chunks with topics and 512-dim embeddings.

    Schema: {video_id, start_time, end_time, topic, transcript, embedding}
    """
    chunks = []

    if segments:
        # Group segments into ~chunk_window_sec blocks for coherent semantic context
        current_start = segments[0]["start_time"]
        current_end = segments[0]["end_time"]
        current_texts = [segments[0]["text"]]

        for seg in segments[1:]:
            if (seg["end_time"] - current_start) <= chunk_window_sec:
                current_texts.append(seg["text"])
                current_end = seg["end_time"]
            else:
                transcript_block = " ".join(current_texts).strip()
                topic_preview = transcript_block[:40] + ("..." if len(transcript_block) > 40 else "")
                embedding = generate_transcript_embedding(transcript_block)

                chunks.append({
                    "video_id": video_id,
                    "start_time": round(current_start, 2),
                    "end_time": round(current_end, 2),
                    "topic": topic_preview,
                    "transcript": transcript_block,
                    "embedding": embedding,
                })

                current_start = seg["start_time"]
                current_end = seg["end_time"]
                current_texts = [seg["text"]]

        if current_texts:
            transcript_block = " ".join(current_texts).strip()
            topic_preview = transcript_block[:40] + ("..." if len(transcript_block) > 40 else "")
            embedding = generate_transcript_embedding(transcript_block)
            chunks.append({
                "video_id": video_id,
                "start_time": round(current_start, 2),
                "end_time": round(current_end, 2),
                "topic": topic_preview,
                "transcript": transcript_block,
                "embedding": embedding,
            })
    else:
        # If video is silent or has no speech, generate visual temporal chunks from keyframes
        for kf in keyframes:
            t_start = kf["timestamp_sec"]
            t_end = min(t_start + 10.0, duration_sec)
            desc = f"Visual segment at timestamp {int(t_start)}s to {int(t_end)}s"
            embedding = generate_transcript_embedding(desc)

            chunks.append({
                "video_id": video_id,
                "start_time": round(t_start, 2),
                "end_time": round(t_end, 2),
                "topic": f"Visual Scene [{int(t_start)}s-{int(t_end)}s]",
                "transcript": desc,
                "embedding": embedding,
            })

    return chunks


def analyze_video(
    video_path: Union[str, Path],
    force_reprocess: bool = False,
    interval_sec: float = 10.0,
) -> dict[str, Any]:
    """Processes a video file into keyframes, transcripts, and timestamped chunks.

    Results are cached to disk so repeat requests for the same video_id return instantly.

    Args:
        video_path: Path to video file.
        force_reprocess (bool): If True, bypasses cache and re-analyzes.
        interval_sec (float): Keyframe extraction interval (default: 10s).

    Returns:
        dict[str, Any]: Video analysis metadata, keyframes, and timestamped chunks.
    """
    video_path = Path(video_path).resolve()
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    video_id = compute_video_id(video_path)
    cache_file = CACHE_DIR / f"{video_id}.json"

    # 1. Check Cache
    if not force_reprocess and cache_file.exists():
        logger.info(f"Loading cached analysis for video_id: {video_id}")
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
            cached_data["cached"] = True
            return cached_data
        except Exception as e:
            logger.warning(f"Failed to read cache for {video_id}: {e}")

    logger.info(f"Processing video {video_path.name} (video_id: {video_id})...")

    # 2. Extract Video Stream Metadata
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_sec = round(total_frames / fps, 2) if fps > 0 else 0.0
    cap.release()

    # 3. Extract Keyframes at ~10s intervals
    logger.info(f"Extracting keyframes every {interval_sec}s...")
    keyframes = extract_keyframes(video_path, video_id, interval_sec=interval_sec)

    # 4. Transcribe Audio
    logger.info("Extracting and transcribing audio track...")
    segments = transcribe_audio(video_path)
    full_transcript = " ".join(s["text"] for s in segments).strip()

    # 5. Create Timestamped Semantic Chunks with Embeddings
    logger.info("Generating timestamped semantic chunks and embeddings...")
    chunks = create_timestamped_chunks(
        video_id=video_id,
        segments=segments,
        keyframes=keyframes,
        duration_sec=duration_sec,
    )

    result_payload = {
        "video_id": video_id,
        "filename": video_path.name,
        "duration_seconds": duration_sec,
        "fps": round(fps, 2),
        "resolution": f"{width}x{height}",
        "total_keyframes": len(keyframes),
        "keyframes": keyframes,
        "full_transcript": full_transcript,
        "segments": segments,
        "chunks_count": len(chunks),
        "chunks": chunks,
        "cached": False,
    }


    # 6. Save to Disk Cache
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(result_payload, f, indent=2)
        logger.info(f"Cached video analysis to {cache_file}")
    except Exception as e:
        logger.warning(f"Failed to write cache for {video_id}: {e}")

    # 7. Index Segments to Azure AI Search
    try:
        from services.video.search import index_video_chunks_to_search
        indexed_count = index_video_chunks_to_search(video_id, chunks)
        result_payload["indexed_segments_count"] = indexed_count
    except Exception as e:
        logger.warning(f"Azure AI Search indexing for video '{video_id}' skipped/failed: {e}")
        result_payload["indexed_segments_count"] = 0

    return result_payload
