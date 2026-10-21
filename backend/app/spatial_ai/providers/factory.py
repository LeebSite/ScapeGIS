"""
Spatial AI Provider Factory

Creates provider instances (GeminiProvider or GroqProvider) based on
application configuration or explicit provider selection.
"""
from typing import Optional

from app.core.config import settings
from app.spatial_ai.exceptions import ProviderConfigurationError
from app.spatial_ai.providers.base import BaseSpatialAIProvider
from app.spatial_ai.providers.gemini_provider import GeminiProvider
from app.spatial_ai.providers.groq_provider import GroqProvider


def create_spatial_ai_provider(provider_name: Optional[str] = None) -> BaseSpatialAIProvider:
    """
    Factory function to instantiate the active BaseSpatialAIProvider.
    Defaults to settings.SPATIAL_AI_PROVIDER ('gemini').
    """
    name = (provider_name or getattr(settings, "SPATIAL_AI_PROVIDER", "gemini")).lower().strip()

    if name == "gemini":
        return GeminiProvider(
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.GEMINI_MODEL,
            timeout_seconds=settings.GEMINI_TIMEOUT_SECONDS,
        )
    elif name == "groq":
        return GroqProvider(
            api_key=settings.GROQ_API_KEY,
            model_name=settings.GROQ_MODEL,
            timeout_seconds=settings.GROQ_TIMEOUT_SECONDS,
            reasoning_effort=settings.GROQ_REASONING_EFFORT,
            max_completion_tokens=settings.GROQ_MAX_COMPLETION_TOKENS,
        )
    else:
        raise ProviderConfigurationError(
            f"Unsupported spatial AI provider '{name}'. Supported providers: 'gemini', 'groq'."
        )
