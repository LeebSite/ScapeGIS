"""
Spatial AI Exceptions
"""

class SpatialAIError(Exception):
    """Base exception for all Spatial AI operations."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class SpatialAIAuthorizationError(SpatialAIError):
    """Raised when user lacks permission to workspace, project, or GIS dataset."""
    pass


class SemanticResolutionError(SpatialAIError):
    """Raised when a semantic category or subcategory cannot be resolved to an authorized layer."""
    pass


class ToolExecutionError(SpatialAIError):
    """Raised when a spatial tool fails during execution."""
    pass


class ToolNotFoundError(SpatialAIError):
    """Raised when an unrecognized tool name is requested."""
    pass