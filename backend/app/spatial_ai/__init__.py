"""
ScapeGIS Spatial AI Module

Controlled tool contract layer for AI-driven spatial reasoning.
Provides a registry of spatial tools that delegate to verified
PostGIS services, with mandatory authorization and provenance tracking.

Module 2A: Spatial AI Context & Tool Contract
"""
from app.spatial_ai.tool_registry import default_registry, SpatialAIToolRegistry
from app.spatial_ai.context import build_spatial_ai_context, SpatialAIContext
from app.spatial_ai.exceptions import (
    SpatialAIError,
    SpatialAIAuthorizationError,
    SemanticResolutionError,
    ToolExecutionError,
    ToolNotFoundError,
)

__all__ = [
    "default_registry",
    "SpatialAIToolRegistry",
    "build_spatial_ai_context",
    "SpatialAIContext",
    "SpatialAIError",
    "SpatialAIAuthorizationError",
    "SemanticResolutionError",
    "ToolExecutionError",
    "ToolNotFoundError",
]
