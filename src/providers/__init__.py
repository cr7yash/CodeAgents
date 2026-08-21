"""LLM access through the Portkey AI gateway."""

from functools import lru_cache

from src.config.settings import get_settings
from src.providers.base import GenerationConfig, GenerationResult, LLMProvider
from src.providers.portkey_provider import PortkeyProvider

__all__ = [
    "GenerationConfig",
    "GenerationResult",
    "LLMProvider",
    "PortkeyProvider",
    "get_provider",
]


@lru_cache
def get_provider() -> PortkeyProvider:
    """Get the cached gateway provider instance."""
    settings = get_settings()
    return PortkeyProvider(
        api_key=settings.portkey_api_key,
        base_url=settings.portkey_base_url,
    )
