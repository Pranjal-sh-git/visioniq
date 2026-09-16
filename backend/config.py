"""Configuration settings for VisionIQ backend.

Loads all environment variables required for Azure AI Foundry, Azure AI Search,
Azure Content Understanding, and Azure Storage. Secrets are never hardcoded.
"""

from functools import lru_cache
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
ENV_FILE_ROOT = ROOT_DIR / ".env"
ENV_FILE_LOCAL = BASE_DIR / ".env"


class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "VisionIQ Backend"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Azure AI Foundry & Agent Service
    AZURE_FOUNDRY_ENDPOINT: str = os.getenv("AZURE_FOUNDRY_ENDPOINT", "")
    AZURE_FOUNDRY_KEY: str = os.getenv("AZURE_FOUNDRY_KEY", "")

    # Azure AI Search
    AZURE_SEARCH_ENDPOINT: str = os.getenv("AZURE_SEARCH_ENDPOINT", "")
    AZURE_SEARCH_KEY: str = os.getenv("AZURE_SEARCH_KEY", "")

    # Azure Content Understanding
    AZURE_CONTENT_UNDERSTANDING_ENDPOINT: str = os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT", "")
    AZURE_CONTENT_UNDERSTANDING_KEY: str = os.getenv("AZURE_CONTENT_UNDERSTANDING_KEY", "")

    # Azure Blob Storage
    AZURE_STORAGE_CONNECTION_STRING: str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")

    model_config = SettingsConfigDict(
        env_file=(str(ENV_FILE_ROOT), str(ENV_FILE_LOCAL), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Returns cached instance of the application settings."""
    return Settings()


settings = get_settings()
