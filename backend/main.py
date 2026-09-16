"""VisionIQ FastAPI Application Entrypoint.

Scaffolds the REST API with CORS middleware configured for the Vite frontend
and a health check endpoint.
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
except ImportError:
    from backend.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="Multimodal content intelligence agent API",
    version="0.1.0",
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        dict: Status confirmation object {"status": "ok"}
    """
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
