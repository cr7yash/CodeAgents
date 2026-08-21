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

    # LLM Provider (Portkey AI gateway)
    portkey_api_key: str = ""
    portkey_base_url: str = "https://api.portkey.ai/v1"

    # Model settings
    default_model: str = "claude-sonnet-4-5"
    temperature: float = 0.7
    max_output_tokens: int = 4000
    reasoning_effort: str | None = None

    # Per-agent model overrides; fall back to default_model when unset
    quality_model: str | None = None
    security_model: str | None = None
    performance_model: str | None = None
    documentation_model: str | None = None

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
