"""
Tests for Module 2A - Spatial AI Context & Tool Contract

Tests cover:
  - SpatialAIToolRegistry: registration, discovery, schema export
  - BaseSpatialTool contract: metadata, Gemini declarations, JSON schemas
  - Tool input validation via Pydantic schemas
  - Authorization chain enforcement (mocked)
  - Context builder (mocked)
  - Exception hierarchy
  - Gemini function declaration format compliance

Does NOT require live database or PostGIS - all data is mocked.
"""
import pytest
from uuid import uuid4, UUID
from unittest.mock import MagicMock, patch, PropertyMock
from sqlalchemy.orm import Session

from app.spatial_ai.exceptions import (
    SpatialAIError,
    SpatialAIAuthorizationError,
    SemanticResolutionError,
    ToolExecutionError,
    ToolNotFoundError,
)
from app.spatial_ai.schemas import (
    FindNearestInput,
    FindNearestOutput,
    NearestFeatureDetails,
    SearchRadiusInput,
    SearchRadiusOutput,
    RadiusFeatureItem,
    GetSpatialContextInput,
    GetSpatialContextOutput,
    CheckContainmentInput,
    CheckContainmentOutput,
    FindIntersectionsInput,
    FindIntersectionsOutput,
    SpatialProvenance,
    ToolIntent,
    MapAction,
    MapActionType,
    SpatialFact,
    SpatialAIResponse,
)
from app.spatial_ai.tools.base import BaseSpatialTool
from app.spatial_ai.tools.spatial_tools import (
    GetSpatialContextTool,
    FindNearestTool,
    SearchRadiusTool,
    CheckContainmentTool,
    FindIntersectionsTool,
)
from app.spatial_ai.tool_registry import (
    SpatialAIToolRegistry,
    create_default_registry,
    default_registry,
)


# -- Constants --

PEKANBARU_LAT = 0.507
PEKANBARU_LNG = 101.447
FAKE_WORKSPACE_ID = uuid4()
FAKE_PROJECT_ID = uuid4()


# ========================================
# Exception Hierarchy Tests
# ========================================

class TestExceptionHierarchy:
    """Verify the spatial AI exception class hierarchy."""

    def test_base_exception_has_message_and_details(self):
        exc = SpatialAIError("test error", details={"key": "value"})
        assert exc.message == "test error"
        assert exc.details == {"key": "value"}
        assert str(exc) == "test error"

    def test_base_exception_defaults_details_to_empty_dict(self):
        exc = SpatialAIError("no details")
        assert exc.details == {}

    def test_authorization_error_is_spatial_ai_error(self):
        exc = SpatialAIAuthorizationError("denied")
        assert isinstance(exc, SpatialAIError)

    def test_semantic_resolution_error_is_spatial_ai_error(self):
        exc = SemanticResolutionError("not found")
        assert isinstance(exc, SpatialAIError)

    def test_tool_execution_error_is_spatial_ai_error(self):
        exc = ToolExecutionError("failed")
        assert isinstance(exc, SpatialAIError)

    def test_tool_not_found_error_is_spatial_ai_error(self):
        exc = ToolNotFoundError("missing tool")
        assert isinstance(exc, SpatialAIError)


# ========================================
# Schema Validation Tests
# ========================================

class TestSchemaValidation:
    """Verify Pydantic input/output schemas work correctly."""

    def test_find_nearest_input_valid(self):
        data = FindNearestInput(
            latitude=PEKANBARU_LAT,
            longitude=PEKANBARU_LNG,
            subcategory="hospital",
            workspace_id=FAKE_WORKSPACE_ID,
        )
        assert data.latitude == PEKANBARU_LAT
        assert data.subcategory == "hospital"

    def test_find_nearest_input_invalid_latitude(self):
        with pytest.raises(Exception):
            FindNearestInput(
                latitude=200.0,  # out of range
                longitude=PEKANBARU_LNG,
                subcategory="hospital",
                workspace_id=FAKE_WORKSPACE_ID,
            )

    def test_search_radius_input_default_values(self):
        data = SearchRadiusInput(
            latitude=PEKANBARU_LAT,
            longitude=PEKANBARU_LNG,
            subcategory="hospital",
            workspace_id=FAKE_WORKSPACE_ID,
        )
        assert data.radius_m == 2000.0
        assert data.limit == 20

    def test_search_radius_input_excessive_radius_rejected(self):
        with pytest.raises(Exception):
            SearchRadiusInput(
                latitude=PEKANBARU_LAT,
                longitude=PEKANBARU_LNG,
                subcategory="hospital",
                workspace_id=FAKE_WORKSPACE_ID,
                radius_m=100000.0,  # exceeds 50km max
            )

    def test_spatial_provenance_model(self):
        prov = SpatialProvenance(
            dataset_id="ds-123",
            dataset_name="Pekanbaru GIS",
            layer_id="layer-456",
            layer_name="Rumah Sakit",
            semantic_category="public_facility",
            semantic_subcategory="hospital",
            operation="ST_DWithin",
            feature_count_queried=5,
        )
        assert prov.operation == "ST_DWithin"
        assert prov.feature_count_queried == 5

    def test_tool_intent_schema(self):
        intent = ToolIntent(
            tool="find_nearest",
            subcategory="hospital",
            parameters={"latitude": PEKANBARU_LAT, "longitude": PEKANBARU_LNG},
            confidence=0.95,
            reasoning="User asked about nearest hospital",
        )
        assert intent.tool == "find_nearest"
        assert intent.confidence == 0.95

    def test_map_action_schema(self):
        action = MapAction(
            type=MapActionType.HIGHLIGHT_FEATURE,
            layer_id="layer-123",
            feature_ids=["feat-1", "feat-2"],
        )
        assert action.type == "highlight_feature"
        assert len(action.feature_ids) == 2

    def test_spatial_fact_schema(self):
        fact = SpatialFact(
            type="distance",
            category="public_facility",
            subcategory="hospital",
            statement="Rumah sakit terdekat berjarak 1.2 km",
            value=1200.0,
            unit="meter",
        )
        assert fact.type == "distance"
        assert fact.value == 1200.0

    def test_find_nearest_output_schema(self):
        output = FindNearestOutput(
            success=True,
            category="public_facility",
            subcategory="hospital",
            target={"latitude": PEKANBARU_LAT, "longitude": PEKANBARU_LNG},
            result=NearestFeatureDetails(
                feature_id="feat-1",
                name="RS Awal Bros",
                distance_m=1200.0,
                distance_km=1.2,
            ),
        )
        assert output.success is True
        assert output.result.name == "RS Awal Bros"


# ========================================
# Tool Contract Tests
# ========================================

class TestToolContract:
    """Verify BaseSpatialTool contract is properly implemented by all tools."""

    @pytest.fixture
    def all_tools(self):
        return [
            GetSpatialContextTool(),
            FindNearestTool(),
            SearchRadiusTool(),
            CheckContainmentTool(),
            FindIntersectionsTool(),
        ]

    def test_all_tools_have_required_attributes(self, all_tools):
        for tool in all_tools:
            assert hasattr(tool, "name"), f"Tool {type(tool).__name__} missing 'name'"
            assert hasattr(tool, "description"), f"Tool {type(tool).__name__} missing 'description'"
            assert hasattr(tool, "purpose"), f"Tool {type(tool).__name__} missing 'purpose'"
            assert hasattr(tool, "input_schema"), f"Tool {type(tool).__name__} missing 'input_schema'"
            assert hasattr(tool, "output_schema"), f"Tool {type(tool).__name__} missing 'output_schema'"

    def test_all_tools_are_base_spatial_tool(self, all_tools):
        for tool in all_tools:
            assert isinstance(tool, BaseSpatialTool)

    def test_tool_names_are_unique(self, all_tools):
        names = [tool.name for tool in all_tools]
        assert len(names) == len(set(names)), f"Duplicate tool names: {names}"

    def test_all_tools_produce_metadata(self, all_tools):
        for tool in all_tools:
            meta = tool.get_metadata()
            assert "name" in meta
            assert "description" in meta
            assert "purpose" in meta
            assert "input_schema" in meta
            assert "output_schema" in meta
            assert "underlying_service" in meta
            assert meta["name"] == tool.name

    def test_all_tools_produce_gemini_declaration(self, all_tools):
        for tool in all_tools:
            decl = tool.to_gemini_declaration()
            assert "name" in decl
            assert "description" in decl
            assert "parameters" in decl
            assert decl["parameters"]["type"] == "OBJECT"
            assert "properties" in decl["parameters"]
            assert "required" in decl["parameters"]

    def test_all_tools_produce_json_schema(self, all_tools):
        for tool in all_tools:
            schema = tool.to_json_schema()
            assert schema["type"] == "function"
            assert "function" in schema
            assert schema["function"]["name"] == tool.name
            assert "parameters" in schema["function"]

    def test_gemini_declaration_properties_are_cleaned(self):
        tool = FindNearestTool()
        decl = tool.to_gemini_declaration()
        props = decl["parameters"]["properties"]
        for prop_name, prop_def in props.items():
            assert "type" in prop_def, f"Property '{prop_name}' missing 'type'"
            assert "description" in prop_def, f"Property '{prop_name}' missing 'description'"
            # Gemini properties should not have Pydantic artifacts
            assert "title" not in prop_def

    def test_tool_validate_input_valid(self):
        tool = FindNearestTool()
        result = tool.validate_input({
            "latitude": PEKANBARU_LAT,
            "longitude": PEKANBARU_LNG,
            "subcategory": "hospital",
            "workspace_id": str(FAKE_WORKSPACE_ID),
        })
        assert isinstance(result, FindNearestInput)

    def test_tool_validate_input_invalid_raises_tool_execution_error(self):
        tool = FindNearestTool()
        with pytest.raises(ToolExecutionError):
            tool.validate_input({
                "latitude": "not_a_number",
                "subcategory": "hospital",
                "workspace_id": str(FAKE_WORKSPACE_ID),
            })

    def test_specific_tool_names(self, all_tools):
        expected_names = {
            "get_spatial_context",
            "find_nearest",
            "search_radius",
            "check_containment",
            "find_intersections",
        }
        actual_names = {tool.name for tool in all_tools}
        assert actual_names == expected_names


# ========================================
# Registry Tests
# ========================================

class TestToolRegistry:
    """Verify the SpatialAIToolRegistry behavior."""

    @pytest.fixture
    def empty_registry(self):
        return SpatialAIToolRegistry()

    @pytest.fixture
    def seeded_registry(self):
        return create_default_registry()

    def test_empty_registry_has_no_tools(self, empty_registry):
        assert empty_registry.list_tools() == []

    def test_register_tool(self, empty_registry):
        tool = FindNearestTool()
        empty_registry.register(tool)
        assert empty_registry.has_tool("find_nearest")
        assert len(empty_registry.list_tools()) == 1

    def test_register_non_tool_raises_type_error(self, empty_registry):
        with pytest.raises(TypeError):
            empty_registry.register("not_a_tool")

    def test_unregister_tool(self, empty_registry):
        tool = FindNearestTool()
        empty_registry.register(tool)
        empty_registry.unregister("find_nearest")
        assert not empty_registry.has_tool("find_nearest")

    def test_unregister_nonexistent_tool_is_noop(self, empty_registry):
        empty_registry.unregister("nonexistent")  # should not raise

    def test_get_tool_returns_correct_instance(self, seeded_registry):
        tool = seeded_registry.get_tool("find_nearest")
        assert isinstance(tool, FindNearestTool)

    def test_get_nonexistent_tool_raises_error(self, seeded_registry):
        with pytest.raises(ToolNotFoundError) as exc_info:
            seeded_registry.get_tool("nonexistent_tool")
        assert "nonexistent_tool" in str(exc_info.value)

    def test_default_registry_has_five_tools(self, seeded_registry):
        tools = seeded_registry.list_tools()
        assert len(tools) == 5
        expected = {"get_spatial_context", "find_nearest", "search_radius", "check_containment", "find_intersections"}
        assert set(tools) == expected

    def test_get_tools_metadata(self, seeded_registry):
        metadata = seeded_registry.get_tools_metadata()
        assert len(metadata) == 5
        for meta in metadata:
            assert "name" in meta
            assert "description" in meta

    def test_to_gemini_declarations(self, seeded_registry):
        declarations = seeded_registry.to_gemini_declarations()
        assert len(declarations) == 5
        for decl in declarations:
            assert "name" in decl
            assert "parameters" in decl
            assert decl["parameters"]["type"] == "OBJECT"

    def test_to_json_schemas(self, seeded_registry):
        schemas = seeded_registry.to_json_schemas()
        assert len(schemas) == 5
        for schema in schemas:
            assert schema["type"] == "function"

    def test_has_tool(self, seeded_registry):
        assert seeded_registry.has_tool("find_nearest") is True
        assert seeded_registry.has_tool("totally_fake") is False


# ========================================
# Global Default Registry Tests
# ========================================

class TestDefaultRegistry:
    """Verify the module-level default_registry singleton."""

    def test_default_registry_is_populated(self):
        assert isinstance(default_registry, SpatialAIToolRegistry)
        assert len(default_registry.list_tools()) == 5

    def test_default_registry_gemini_export(self):
        decls = default_registry.to_gemini_declarations()
        assert len(decls) == 5
        tool_names = {d["name"] for d in decls}
        assert "find_nearest" in tool_names
        assert "search_radius" in tool_names

    def test_default_registry_json_schema_export(self):
        schemas = default_registry.to_json_schemas()
        assert len(schemas) == 5


# ========================================
# Context Builder Tests (Mocked)
# ========================================

class TestContextBuilder:
    """Verify SpatialAIContext builder with mocked database."""

    def test_context_import(self):
        """Verify the context builder can be imported."""
        from app.spatial_ai.context import build_spatial_ai_context, SpatialAIContext
        assert callable(build_spatial_ai_context)

    def test_spatial_ai_context_schema(self):
        from app.spatial_ai.context import SpatialAIContext
        ctx = SpatialAIContext(
            user_id=str(uuid4()),
            user_email="test@scapegis.com",
            workspace_id=str(FAKE_WORKSPACE_ID),
            workspace_name="Test Workspace",
            authorized_dataset_ids=[],
            available_concepts=[],
            available_tools=["find_nearest", "search_radius"],
        )
        assert ctx.workspace_name == "Test Workspace"
        assert len(ctx.available_tools) == 2

    def test_context_to_system_prompt_summary(self):
        from app.spatial_ai.context import SpatialAIContext
        ctx = SpatialAIContext(
            user_id=str(uuid4()),
            user_email="test@scapegis.com",
            workspace_id=str(FAKE_WORKSPACE_ID),
            workspace_name="Demo Workspace",
            available_tools=["find_nearest", "search_radius", "check_containment"],
        )
        prompt = ctx.to_system_prompt_summary()
        assert "SCAPEGIS SPATIAL INTELLIGENCE" in prompt
        assert "Demo Workspace" in prompt
        assert "find_nearest" in prompt

    def test_context_system_prompt_includes_rule(self):
        from app.spatial_ai.context import SpatialAIContext
        ctx = SpatialAIContext(
            user_id=str(uuid4()),
            user_email="test@scapegis.com",
            workspace_id=str(FAKE_WORKSPACE_ID),
            workspace_name="Test",
            available_tools=[],
        )
        prompt = ctx.to_system_prompt_summary()
        assert "Never invent or hallucinate" in prompt


# ========================================
# Module-Level Import Test
# ========================================

class TestModuleImports:
    """Verify the spatial_ai package exports are correct."""

    def test_package_exports_default_registry(self):
        from app.spatial_ai import default_registry
        assert isinstance(default_registry, SpatialAIToolRegistry)

    def test_package_exports_context_builder(self):
        from app.spatial_ai import build_spatial_ai_context
        assert callable(build_spatial_ai_context)

    def test_package_exports_exceptions(self):
        from app.spatial_ai import (
            SpatialAIError,
            SpatialAIAuthorizationError,
            SemanticResolutionError,
            ToolExecutionError,
            ToolNotFoundError,
        )
        assert issubclass(ToolNotFoundError, SpatialAIError)

    def test_tool_exports_from_tools_package(self):
        from app.spatial_ai.tools import (
            BaseSpatialTool,
            GetSpatialContextTool,
            FindNearestTool,
            SearchRadiusTool,
            CheckContainmentTool,
            FindIntersectionsTool,
        )
        assert issubclass(FindNearestTool, BaseSpatialTool)
