"""
Spatial AI Schemas and Tool Contracts

Defines all input, output, provenance, intent, map action,
and AI response schemas. Provider-agnostic and fully serializable.
"""
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


# â”€â”€ Coordinates â”€â”€

class CoordinateTarget(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude (WGS 84)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude (WGS 84)")


# â”€â”€ Provenance / Source Attribution â”€â”€

class SpatialProvenance(BaseModel):
    """
    Retains strict lineage for all facts delivered to an LLM.
    Ensures that every distance, count, or area name maps back
    to an authorized PostGIS dataset and layer.
    """
    dataset_id: str = Field(..., description="ID of the GIS dataset")
    dataset_name: Optional[str] = Field(None, description="Human-readable name of the dataset")
    layer_id: str = Field(..., description="UUID of the GIS layer")
    layer_name: str = Field(..., description="Technical table/layer name in PostGIS")
    semantic_category: str = Field(..., description="High-level category (e.g. transportation)")
    semantic_subcategory: str = Field(..., description="Specific concept (e.g. hospital)")
    operation: str = Field(..., description="PostGIS operation (e.g. ST_DistanceSphere, ST_DWithin)")
    feature_count_queried: Optional[int] = Field(None, description="Number of features evaluated")

    model_config = ConfigDict(from_attributes=True)


# â”€â”€ Tool Input Schemas â”€â”€

class FindNearestInput(BaseModel):
    """Input parameters for find_nearest spatial tool."""
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude of target location")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude of target location")
    subcategory: str = Field(..., description="Semantic concept (e.g. 'hospital', 'arterial_road', 'mosque')")
    workspace_id: UUID = Field(..., description="Workspace ID for scoping authorization")
    project_id: Optional[UUID] = Field(None, description="Optional Project ID context")
    max_distance_m: Optional[float] = Field(None, gt=0, le=50000.0, description="Optional max search distance in meters")


class SearchRadiusInput(BaseModel):
    """Input parameters for search_radius spatial tool."""
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude of target location")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude of target location")
    subcategory: str = Field(..., description="Semantic concept (e.g. 'hospital', 'mosque', 'clinic')")
    radius_m: float = Field(2000.0, gt=0.0, le=50000.0, description="Search radius in meters (default 2000)")
    workspace_id: UUID = Field(..., description="Workspace ID for scoping authorization")
    project_id: Optional[UUID] = Field(None, description="Optional Project ID context")
    limit: int = Field(20, gt=0, le=100, description="Maximum number of features to return")


class GetSpatialContextInput(BaseModel):
    """Input parameters for get_spatial_context spatial tool."""
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude of target location")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude of target location")
    workspace_id: UUID = Field(..., description="Workspace ID for scoping authorization")
    project_id: Optional[UUID] = Field(None, description="Optional Project ID context")


class CheckContainmentInput(BaseModel):
    """Input parameters for check_containment spatial tool."""
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude of target location")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude of target location")
    workspace_id: UUID = Field(..., description="Workspace ID for scoping authorization")
    subcategory: str = Field("administrative_boundary", description="Semantic subcategory for polygon boundary")
    layer_id: Optional[UUID] = Field(None, description="Specific layer ID if known")
    project_id: Optional[UUID] = Field(None, description="Optional Project ID context")


class FindIntersectionsInput(BaseModel):
    """Input parameters for find_intersections spatial tool."""
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude of target location")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude of target location")
    subcategory: str = Field(..., description="Semantic concept (e.g. 'arterial_road', 'collector_road')")
    workspace_id: UUID = Field(..., description="Workspace ID for scoping authorization")
    buffer_m: float = Field(100.0, gt=0.0, le=5000.0, description="Buffer distance in meters (default 100)")
    project_id: Optional[UUID] = Field(None, description="Optional Project ID context")
    limit: int = Field(20, gt=0, le=50, description="Maximum number of features")


# â”€â”€ Tool Output Schemas â”€â”€

class NearestFeatureDetails(BaseModel):
    feature_id: str
    name: Optional[str] = None
    distance_m: float
    distance_km: float
    properties: Dict[str, Any] = Field(default_factory=dict)


class FindNearestOutput(BaseModel):
    success: bool
    category: str
    subcategory: str
    target: Dict[str, float]
    result: Optional[NearestFeatureDetails] = None
    source: Optional[SpatialProvenance] = None
    error: Optional[str] = None


class RadiusFeatureItem(BaseModel):
    feature_id: str
    name: Optional[str] = None
    distance_m: float
    distance_km: float
    properties: Dict[str, Any] = Field(default_factory=dict)


class SearchRadiusOutput(BaseModel):
    success: bool
    subcategory: str
    target: Dict[str, float]
    radius_m: float
    count: int
    features: List[RadiusFeatureItem] = Field(default_factory=list)
    sources: List[SpatialProvenance] = Field(default_factory=list)
    error: Optional[str] = None


class CheckContainmentOutput(BaseModel):
    success: bool
    target: Dict[str, float]
    contained: bool
    area_name: Optional[str] = None
    feature_id: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    source: Optional[SpatialProvenance] = None
    error: Optional[str] = None


class FindIntersectionsOutput(BaseModel):
    success: bool
    target: Dict[str, float]
    buffer_m: float
    count: int
    features: List[Dict[str, Any]] = Field(default_factory=list)
    sources: List[SpatialProvenance] = Field(default_factory=list)
    error: Optional[str] = None


class GetSpatialContextOutput(BaseModel):
    success: bool
    target: Dict[str, float]
    workspace_id: str
    project_id: Optional[str] = None
    project: Optional[Dict[str, Any]] = None
    authorized_datasets: List[str] = Field(default_factory=list)
    transportation: Dict[str, Any] = Field(default_factory=dict)
    facilities: Dict[str, Any] = Field(default_factory=dict)
    religious: Dict[str, Any] = Field(default_factory=dict)
    administrative: Dict[str, Any] = Field(default_factory=dict)
    facts: List[Dict[str, Any]] = Field(default_factory=list)
    sources: List[SpatialProvenance] = Field(default_factory=list)
    warning: Optional[str] = None
    error: Optional[str] = None


# â”€â”€ Natural Language Tool Intent â”€â”€

class ToolIntent(BaseModel):
    """
    Contract for parsing natural-language intentions into tool calls.
    Produced by the LLM (Gemini) when deciding which tool to invoke.
    """
    tool: str = Field(..., description="Name of the spatial tool to invoke (e.g. 'find_nearest')")
    category: Optional[str] = Field(None, description="Optional high-level category")
    subcategory: Optional[str] = Field(None, description="Semantic concept requested (e.g. 'hospital')")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Raw arguments for tool execution")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score")
    reasoning: Optional[str] = Field(None, description="Explanation for selecting this tool")


# â”€â”€ Map Action Contract â”€â”€

class MapActionType(str, Enum):
    SHOW_LAYER = "show_layer"
    HIDE_LAYER = "hide_layer"
    HIGHLIGHT_FEATURE = "highlight_feature"
    FIT_BOUNDS = "fit_bounds"
    SHOW_MARKER = "show_marker"
    CLEAR_HIGHLIGHT = "clear_highlight"


class MapAction(BaseModel):
    """
    Contract for map manipulations triggered by spatial tool execution
    or AI analytical conclusions.
    """
    type: str = Field(..., description="Action type e.g. 'highlight_feature', 'show_marker'")
    layer_id: Optional[str] = None
    feature_ids: Optional[List[str]] = Field(default_factory=list)
    coordinates: Optional[Dict[str, float]] = None
    bounds: Optional[Dict[str, float]] = None
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict)


# â”€â”€ Structured Spatial Facts â”€â”€

class SpatialFact(BaseModel):
    """
    Atomic, validated spatial fact extracted from PostGIS.
    LLMs must use these facts rather than hallucinating numbers.
    """
    type: str = Field(..., description="Fact type: 'distance', 'count', 'containment', 'accessibility'")
    category: str
    subcategory: str
    statement: str = Field(..., description="Concise Indonesian/English description")
    value: Any = Field(..., description="Numeric or string value")
    unit: Optional[str] = Field(None, description="meter, km, unit, etc.")
    source_layer: Optional[str] = None
    dataset_id: Optional[str] = None


# â”€â”€ AI Response Contract â”€â”€

class SpatialAIResponse(BaseModel):
    """
    Unified response contract for ScapeGIS Spatial AI answers.
    Combines the natural-language response with verifiable facts,
    provenance sources, map actions, and tool trace.
    """
    answer: str = Field(..., description="Natural language explanation synthesized for developer")
    facts: List[SpatialFact] = Field(default_factory=list, description="Ground truth GIS facts from PostGIS")
    sources: List[SpatialProvenance] = Field(default_factory=list, description="Dataset/Layer provenance")
    map_actions: List[MapAction] = Field(default_factory=list, description="Actions frontend map should execute")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="Audit trace of tools called")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model: Optional[str] = Field(None, description="AI model that generated the answer")


# ── Analysis Request Contract ──

class SpatialAIAnalysisRequest(BaseModel):
    """
    Request payload for the spatial AI analysis endpoint.
    Used for synchronous reasoning and tool execution.
    """
    workspace_id: UUID = Field(..., description="Workspace ID for scoping multi-tenant access")
    project_id: Optional[UUID] = Field(None, description="Optional project context ID")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Target location latitude (-90 to 90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Target location longitude (-180 to 180)")
    message: str = Field(..., min_length=1, max_length=2000, description="Natural language question or request from property developer")

# ── Chat Request & History Contracts ──

class ChatMessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    role: ChatMessageRole = Field(..., description="Role of message author ('user' or 'assistant')")
    content: str = Field(..., min_length=1, max_length=2000, description="Text content of the message")

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Message content cannot be empty or only whitespace.")
        return s


class SpatialAIChatRequest(BaseModel):
    """
    Request payload for the multi-turn Spatial AI chat endpoint.
    Includes current user message, optional coordinate anchor,
    and bounded conversation history.
    """
    workspace_id: UUID = Field(..., description="Workspace ID for scoping multi-tenant access")
    project_id: Optional[UUID] = Field(None, description="Optional project context ID")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Optional target location latitude (-90 to 90)")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Optional target location longitude (-180 to 180)")
    message: str = Field(..., min_length=1, max_length=2000, description="Current user natural language message")
    history: List[ChatMessage] = Field(
        default_factory=list,
        max_length=10,
        description="Recent conversation turns (bounded to a maximum of 10 messages)",
    )

    @field_validator("message")
    @classmethod
    def validate_message_not_empty(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("User message cannot be empty or only whitespace.")
        return s

    @model_validator(mode="after")
    def validate_coordinates(self) -> "SpatialAIChatRequest":
        if (self.latitude is not None and self.longitude is None) or (
            self.latitude is None and self.longitude is not None
        ):
            raise ValueError("Both latitude and longitude must be provided together.")
        return self
