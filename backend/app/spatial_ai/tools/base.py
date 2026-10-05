"""
Base Spatial Tool Contract

Abstract base class for all AI-callable spatial tools.
Enforces authorization, input validation, execution contract,
and conversion to Gemini/OpenAI tool calling schemas.
"""
from abc import ABC, abstractmethod
from typing import Type, Dict, Any, List, Optional
from uuid import UUID
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.spatial_ai.exceptions import (
    SpatialAIAuthorizationError,
    ToolExecutionError,
    SemanticResolutionError,
)
from app.spatial_ai.context import (
    validate_user_workspace_access,
    validate_project_access,
    get_authorized_dataset_ids,
)


class BaseSpatialTool(ABC):
    """
    Base contract for all controlled spatial tools callable by an AI Agent.
    Strictly forbids raw SQL in tool logic; all calls delegate to
    existing verified spatial services.
    """
    name: str
    description: str
    purpose: str
    category: str = "spatial_analysis"
    input_schema: Type[BaseModel]
    output_schema: Type[BaseModel]
    requires_authorization: bool = True
    underlying_service: str = "spatial_analysis_service"

    def validate_input(self, params: Dict[str, Any]) -> BaseModel:
        """Validates raw dictionary parameters against tool's Pydantic schema."""
        try:
            return self.input_schema(**params)
        except Exception as e:
            raise ToolExecutionError(
                f"Invalid parameters for tool '{self.name}': {str(e)}",
                details={"errors": getattr(e, "errors", lambda: str(e))()},
            )

    def authorize(
        self,
        db: Session,
        user: User,
        workspace_id: UUID,
        project_id: Optional[UUID] = None,
    ) -> List[UUID]:
        """
        Validates the complete authorization chain:
        1. Authenticated user
        2. Workspace membership / Platform Admin
        3. Project workspace containment (if project_id given)
        4. Workspace GIS Dataset entitlement

        Returns list of authorized dataset IDs for this workspace.
        """
        if not self.requires_authorization:
            return []

        validate_user_workspace_access(db, user, workspace_id)

        if project_id:
            validate_project_access(db, workspace_id, project_id)

        auth_ids = get_authorized_dataset_ids(db, workspace_id)
        if not auth_ids:
            raise SpatialAIAuthorizationError(
                f"No active GIS datasets are authorized for workspace '{workspace_id}'.",
                details={"workspace_id": str(workspace_id)},
            )

        return auth_ids

    @abstractmethod
    def execute(
        self,
        db: Session,
        user: User,
        params: Dict[str, Any],
    ) -> BaseModel:
        """
        Executes the spatial tool with full authorization and validation.
        Must return an instance of `self.output_schema`.
        """
        pass

    def to_gemini_declaration(self) -> Dict[str, Any]:
        """
        Exports the tool definition into a format directly compatible
        with Google Gemini function declarations.
        """
        json_schema = self.input_schema.model_json_schema()
        
        # Clean Pydantic title/definitions not needed by Gemini
        properties = json_schema.get("properties", {})
        required = json_schema.get("required", [])

        # Gemini-friendly property definitions
        cleaned_properties = {}
        for prop_name, prop_def in properties.items():
            cleaned_prop = {
                "type": prop_def.get("type", "string"),
                "description": prop_def.get("description", ""),
            }
            if "enum" in prop_def:
                cleaned_prop["enum"] = prop_def["enum"]
            if "default" in prop_def:
                cleaned_prop["default"] = prop_def["default"]
            cleaned_properties[prop_name] = cleaned_prop

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "OBJECT",
                "properties": cleaned_properties,
                "required": required,
            },
        }

    def to_json_schema(self) -> Dict[str, Any]:
        """Exports standard JSON schema for OpenAI or general agent frameworks."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema.model_json_schema(),
            },
        }

    def get_metadata(self) -> Dict[str, Any]:
        """Returns internal registry metadata."""
        return {
            "name": self.name,
            "description": self.description,
            "purpose": self.purpose,
            "category": self.category,
            "input_schema": self.input_schema.__name__,
            "output_schema": self.output_schema.__name__,
            "underlying_service": self.underlying_service,
            "requires_authorization": self.requires_authorization,
        }
