"""
ScapeGIS Spatial AI Module

Controlled tool contract layer for AI-driven spatial reasoning.
Provides a registry of spatial tools that delegate to verified
PostGIS services, with mandatory authorization and provenance tracking.

Module 2A: Spatial AI Context & Tool Contract
Module 2B: Gemini Spatial Reasoning Agent
"""
from app.spatial_ai.tool_registry import default_registry, SpatialAIToolRegistry
from app.spatial_ai.context import build_spatial_ai_context, SpatialAIContext
from app.spatial_ai.providers import (
    BaseSpatialAIProvider,
    GeminiProvider,
    ProviderStepResult,
    ToolCallRequest,
)
from app.spatial_ai.agent import GeminiSpatialAgent
from app.spatial_ai.prompts import build_spatial_ai_system_instruction, BASE_SYSTEM_INSTRUCTION
from app.spatial_ai.exceptions import (
    SpatialAIError,
    SpatialAIAuthorizationError,
    SemanticResolutionError,
    ToolExecutionError,
    ToolNotFoundError,
    ProviderConfigurationError,
    ProviderExecutionError,
    ToolLoopExceededError,
    MalformedModelResponseError,
)

__all__ = [
    "default_registry",
    "SpatialAIToolRegistry",
    "build_spatial_ai_context",
    "SpatialAIContext",
    "BaseSpatialAIProvider",
    "GeminiProvider",
    "ProviderStepResult",
    "ToolCallRequest",
    "GeminiSpatialAgent",
    "build_spatial_ai_system_instruction",
    "BASE_SYSTEM_INSTRUCTION",
    "SpatialAIError",
    "SpatialAIAuthorizationError",
    "SemanticResolutionError",
    "ToolExecutionError",
    "ToolNotFoundError",
    "ProviderConfigurationError",
    "ProviderExecutionError",
    "ToolLoopExceededError",
    "MalformedModelResponseError",
]
