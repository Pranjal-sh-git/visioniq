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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

app = FastAPI(
    title=settings.APP_NAME,
    description="Multimodal content intelligence agent API",
    version="0.1.0",
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



@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        dict: Status confirmation object {"status": "ok"}
    """
    return {"status": "ok"}


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

