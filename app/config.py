"""Application configuration settings."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables with safe defaults."""

    app_name: str = os.getenv("APP_NAME", "Insurance Data Pipeline API")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/pipeline.db")
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))


settings = Settings()
