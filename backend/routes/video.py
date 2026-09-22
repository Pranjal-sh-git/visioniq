"""Video analysis, temporal search, and summary API route definitions."""

import logging
from pathlib import Path
import shutil
from typing import Optional
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from services.video.processor import analyze_video, KEYFRAMES_DIR
from services.video.search import grounded_video_qa, generate_video_summary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/video", tags=["Video Intelligence"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "uploads" / "videos"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class AnalyzeVideoRequest(BaseModel):
    file_path: Optional[str] = None
    video_url: Optional[str] = None
    force_reprocess: bool = False


class VideoSearchRequest(BaseModel):
    video_id: str = Field(..., description="ID of the processed video to query against.")
    query: str = Field(..., description="Natural language question or query regarding video content.")
    top_k: int = Field(3, description="Number of candidate segments to inspect.")
    confidence_threshold: float = Field(0.50, description="Minimum confidence score for grounded answer.")


@router.post("/analyze")
async def analyze_video_endpoint(
    file: Optional[UploadFile] = File(None),
    force_reprocess: bool = Query(False),
):
    """Analyzes a video file.

    Extracts audio, transcribes with timestamps, extracts keyframes at ~10s intervals,
    and returns timestamped chunks with embeddings. Results are cached by video_id.
    """
    if file is None:
        raise HTTPException(status_code=400, detail="A video file must be provided via multipart upload.")

    file_path = UPLOAD_DIR / file.filename
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded video file: {e}")

    try:
        result = analyze_video(file_path, force_reprocess=force_reprocess)
        return result
    except Exception as e:
        logger.exception("Error processing video")
        raise HTTPException(status_code=500, detail=f"Video analysis failed: {str(e)}")


@router.post("/analyze-path")
async def analyze_video_path_endpoint(request: AnalyzeVideoRequest):
    """Analyzes a video from an existing local file path."""
    if not request.file_path:
        raise HTTPException(status_code=400, detail="file_path is required.")

    target_path = Path(request.file_path)
    if not target_path.exists():
        raise HTTPException(status_code=404, detail=f"Video file not found at: {request.file_path}")

    try:
        result = analyze_video(target_path, force_reprocess=request.force_reprocess)
        return result
    except Exception as e:
        logger.exception("Error processing video from path")
        raise HTTPException(status_code=500, detail=f"Video analysis failed: {str(e)}")


@router.post("/search")
async def search_video_endpoint(request: VideoSearchRequest):
    """Searches a video's timestamped segments and returns a grounded answer with start_time / end_time.

    If no confident matching segment exists, honestly reports that information was not found.
    """
    if not request.video_id or not request.query:
        raise HTTPException(status_code=400, detail="video_id and query are required.")

    try:
        result = grounded_video_qa(
            video_id=request.video_id,
            question=request.query,
            top_k=request.top_k,
            threshold=request.confidence_threshold,
        )
        return result
    except Exception as e:
        logger.exception("Error during video search")
        raise HTTPException(status_code=500, detail=f"Video search failed: {str(e)}")


@router.get("/{video_id}/summary")
async def get_video_summary_endpoint(
    video_id: str,
    force_regenerate: bool = Query(False),
):
    """Returns an AI-generated structured summary, topics, and key takeaways for a processed video based on its transcript."""
    try:
        summary_data = generate_video_summary(video_id, force_regenerate=force_regenerate)
        return summary_data
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Error generating summary for video {video_id}")
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")


@router.get("/keyframes/{video_id}/{filename}")
async def get_keyframe_image(video_id: str, filename: str):
    """Serves extracted keyframe image for a processed video."""
    image_path = KEYFRAMES_DIR / video_id / filename
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Keyframe image not found.")
    return FileResponse(image_path, media_type="image/jpeg")


@router.get("/file/{filename}")
async def get_uploaded_video_file(filename: str):
    """Serves an uploaded video file for streaming/playback."""
    video_file_path = UPLOAD_DIR / filename
    if not video_file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found.")
    return FileResponse(video_file_path, media_type="video/mp4")

