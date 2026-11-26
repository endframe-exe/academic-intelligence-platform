from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"
BACKEND_ENV = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env."""

    model_config = SettingsConfigDict(
        env_file=[str(ROOT_ENV), str(BACKEND_ENV)],
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "AI Academic Intelligence Platform"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/academic_intelligence"
    JWT_SECRET: str = "dev-only-change-me-in-production-32chars-min"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: str = ""
    UPLOAD_DIR: str = str(Path(__file__).resolve().parents[2] / "uploads")
    MAX_UPLOAD_MB: int = 5

    @property
    def cors_origin_list(self) -> list[str]:
        raw = ",".join(part for part in (self.FRONTEND_URL, self.CORS_ORIGINS) if part)
        origins = [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]
        # Preserve order and deduplicate
        return list(dict.fromkeys(origins)) or ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
