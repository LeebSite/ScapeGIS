"""
Spatial AI Tool Registry

Centralized, extensible registry for all AI-callable spatial tools.
Supports tool discovery, execution routing, and exporting tool
definitions to Google Gemini and OpenAI function-calling formats.
"""
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.spatial_ai.tools.base import BaseSpatialTool
from app.spatial_ai.tools.spatial_tools import (
    GetSpatialContextTool,
    FindNearestTool,
    SearchRadiusTool,
    CheckContainmentTool,
    FindIntersectionsTool,
)
from app.spatial_ai.exceptions import ToolNotFoundError, ToolExecutionError


class SpatialAIToolRegistry:
    """
    Centralized registry of controlled spatial tools.
    Allows dynamic registration, discovery, parameter validation,
    and Gemini function declaration generation.
    """

    def __init__(self):
        self._tools: Dict[str, BaseSpatialTool] = {}

    def register(self, tool: BaseSpatialTool) -> None:
        """Register a new spatial tool."""
        if not isinstance(tool, BaseSpatialTool):
            raise TypeError(f"Expected BaseSpatialTool, got {type(tool)}")
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        """Unregister a tool by name."""
        if name in self._tools:
            del self._tools[name]

    def get_tool(self, name: str) -> BaseSpatialTool:
        """Retrieve a registered tool or raise ToolNotFoundError."""
        tool = self._tools.get(name)
        if not tool:
            raise ToolNotFoundError(
                f"Spatial tool '{name}' is not registered. Available tools: {self.list_tools()}",
                details={"requested_tool": name, "available_tools": self.list_tools()},
            )
        return tool

    def has_tool(self, name: str) -> bool:
        """Check if tool name is registered."""
        return name in self._tools

    def list_tools(self) -> List[str]:
        """Return list of all registered tool names."""
        return list(self._tools.keys())

    def get_tools_metadata(self) -> List[Dict[str, Any]]:
        """Return human-readable metadata for all registered tools."""
        return [tool.get_metadata() for tool in self._tools.values()]

    def to_gemini_declarations(self) -> List[Dict[str, Any]]:
        """
        Generate function declarations directly consumable by the
        Google Gemini Python SDK or REST API.
        """
        return [tool.to_gemini_declaration() for tool in self._tools.values()]

    def to_json_schemas(self) -> List[Dict[str, Any]]:
        """Generate OpenAI/standard function calling tool schemas."""
        return [tool.to_json_schema() for tool in self._tools.values()]

    def execute_tool(
        self,
        name: str,
        db: Session,
        user: User,
        params: Dict[str, Any],
    ) -> Any:
        """
        Executes a registered tool by name with database session and authenticated user.
        Guarantees authorization check and schema validation.
        """
        tool = self.get_tool(name)
        return tool.execute(db=db, user=user, params=params)


# -- Global Default Registry --

def create_default_registry() -> SpatialAIToolRegistry:
    """Creates and seeds the standard ScapeGIS spatial tool registry."""
    registry = SpatialAIToolRegistry()
    registry.register(GetSpatialContextTool())
    registry.register(FindNearestTool())
    registry.register(SearchRadiusTool())
    registry.register(CheckContainmentTool())
    registry.register(FindIntersectionsTool())
    return registry


# Singleton instance for platform-wide usage
default_registry = create_default_registry()
