"""VisionIQ FastAPI Application Entrypoint.

Scaffolds the REST API with CORS middleware configured for the Vite frontend,
health check, and video intelligence endpoints.
"""

import sys
from pathlib import Path

# Add backend directory and project root to sys.path
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
for directory in (str(BACKEND_DIR), str(PROJECT_ROOT)):
    if directory not in sys.path:
        sys.path.insert(0, directory)

from contextlib import asynccontextmanager
import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("visioniq.backend")

try:
    from config import settings
    from routes.video import router as video_router
    from routes.product import router as product_router
    from routes.agent import router as agent_router
except ImportError:
    from backend.config import settings
    from backend.routes.video import router as video_router
    from backend.routes.product import router as product_router
    from backend.routes.agent import router as agent_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-warms local ML embedding models, Whisper ASR, and Azure clients on server startup."""
    logger.info("Pre-warming VisionIQ local ML models, Whisper ASR, and Azure clients...")
    
    app.state.is_ready = False
    allow_download = os.getenv("ALLOW_MODEL_DOWNLOAD", "0").lower() in ("1", "true", "yes")
    if not allow_download:
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"

    # 1. Pre-warm CLIP image embedding model
    try:
        from services.product_search.embeddings import get_embedding_model
        app.state.clip_model = get_embedding_model()
    except Exception as e:
        err_msg = "Model CLIP (clip-ViT-B-32) not cached. Run: python scripts/download_models.py"
        logger.error(f"[STARTUP ERROR] {err_msg}")
        sys.stderr.write(f"\n{err_msg}\n\n")
        raise RuntimeError(err_msg) from None

    # 2. Pre-warm MiniLM dense text retrieval model
    try:
        from services.video.embeddings import get_text_retrieval_model
        app.state.minilm_model = get_text_retrieval_model()
    except Exception as e:
        err_msg = "Model MiniLM (all-MiniLM-L6-v2) not cached. Run: python scripts/download_models.py"
        logger.error(f"[STARTUP ERROR] {err_msg}")
        sys.stderr.write(f"\n{err_msg}\n\n")
        raise RuntimeError(err_msg) from None

    # 3. Pre-warm Whisper ASR speech-to-text pipeline
    try:
        from services.video.processor import get_asr_pipeline
        app.state.whisper_pipeline = get_asr_pipeline()
        if app.state.whisper_pipeline is None and not allow_download:
            err_msg = "Model Whisper (openai/whisper-tiny) not cached. Run: python scripts/download_models.py"
            logger.error(f"[STARTUP ERROR] {err_msg}")
            sys.stderr.write(f"\n{err_msg}\n\n")
            raise RuntimeError(err_msg) from None
    except Exception as e:
        err_msg = "Model Whisper (openai/whisper-tiny) not cached. Run: python scripts/download_models.py"
        logger.error(f"[STARTUP ERROR] {err_msg}")
        sys.stderr.write(f"\n{err_msg}\n\n")
        raise RuntimeError(err_msg) from None

    # 4. Pre-warm AzureOpenAI client
    try:
        from services.llm import get_azure_openai_client
        app.state.openai_client = get_azure_openai_client()
    except Exception as e:
        logger.warning(f"Could not initialize AzureOpenAI client: {e}")
        app.state.openai_client = None

    # 5. Pre-warm Azure AI Search clients
    try:
        from services.product_search.matcher import get_search_client as get_prod_search
        app.state.search_client_product = get_prod_search()
    except Exception as e:
        logger.warning(f"Could not initialize Product SearchClient: {e}")
        app.state.search_client_product = None

    try:
        from services.video.search import get_video_search_client
        app.state.search_client_video = get_video_search_client()
    except Exception as e:
        logger.warning(f"Could not initialize Video SearchClient: {e}")
        app.state.search_client_video = None

    app.state.is_ready = True
    logger.info("VisionIQ server initialized and ready.")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Multimodal content intelligence agent API",
    version="0.1.0",
    lifespan=lifespan,
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register routes
app.include_router(video_router)
app.include_router(product_router)
app.include_router(agent_router)


@app.get("/health")
@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Liveness probe confirming basic API availability."""
    return {"status": "ok"}


@app.get("/health/ready")
@app.get("/api/health/ready")
async def health_ready():
    """Readiness probe endpoint.

    Returns 200 OK only after ML models and backend clients are fully pre-warmed.
    Returns 503 Service Unavailable if initialization is incomplete.
    """
    if getattr(app.state, "is_ready", False):
        return {
            "status": "ready",
            "models_loaded": {
                "clip_vit_b_32": app.state.clip_model is not None,
                "all_minilm_l6_v2": app.state.minilm_model is not None,
                "whisper_tiny": app.state.whisper_pipeline is not None,
            },
            "clients_initialized": {
                "azure_openai": app.state.openai_client is not None,
                "search_client_product": app.state.search_client_product is not None,
                "search_client_video": app.state.search_client_video is not None,
            },
        }
    from fastapi import HTTPException
    raise HTTPException(status_code=503, detail="Models or services are still initializing")


if __name__ == "__main__":
    import uvicorn

    # Robust app target for running directly via `python backend/main.py` or from inside `backend/`
    in_backend_dir = (Path.cwd() / "main.py").exists()
    app_target = "main:app" if in_backend_dir else "backend.main:app"
    reload_dirs = [str(BACKEND_DIR), str(PROJECT_ROOT / "services"), str(PROJECT_ROOT / "agent")]

    uvicorn.run(
        app_target,
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=reload_dirs,
    )

