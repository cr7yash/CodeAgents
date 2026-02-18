"""Application settings using Pydantic."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # LLM Provider
    groq_api_key: str = ""
    llm_provider: str = "groq"

    # Model settings
    default_model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.7

    # Code analysis settings
    max_code_length: int = 50000
    max_line_length: int = 500

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # Database (Phase 5+)
    database_url: str = ""

    # Redis (Phase 5+)
    redis_url: str = ""


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
