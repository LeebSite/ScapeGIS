"""
Tests for Module 2B - Gemini Spatial Reasoning Agent

Covers:
  - Provider abstraction & configuration
  - Mocked Gemini tool calling loop (single-tool and multi-tool)
  - Tool loop limit prevention
  - Multi-tenant authorization enforcement
  - Provenance preservation and MapAction generation
  - API endpoint integration
  - Real Gemini live smoke test (conditionally executed if GEMINI_API_KEY is set)
"""
import os
import pytest
from uuid import uuid4, UUID
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.db.models.user import User
from app.core.config import settings
from app.spatial_ai.exceptions import (
    ProviderConfigurationError,
    ProviderExecutionError,
    SpatialAIAuthorizationError,
    ToolLoopExceededError,
)
from app.spatial_ai.schemas import (
    SpatialAIAnalysisRequest,
    SpatialAIResponse,
    FindNearestOutput,
    NearestFeatureDetails,
    SearchRadiusOutput,
    RadiusFeatureItem,
    SpatialProvenance,
    MapActionType,
)
from app.spatial_ai.providers.base import (
    BaseSpatialAIProvider,
    ProviderStepResult,
    ToolCallRequest,
)
from app.spatial_ai.providers.gemini_provider import GeminiProvider, GeminiSession
from app.spatial_ai.agent import GeminiSpatialAgent
from app.spatial_ai.tool_registry import SpatialAIToolRegistry, default_registry
from app.spatial_ai.context import SpatialAIContext


PEKANBARU_LAT = 0.507
PEKANBARU_LNG = 101.447
FAKE_WORKSPACE_ID = uuid4()
FAKE_PROJECT_ID = uuid4()


class MockAIProvider(BaseSpatialAIProvider):
    """Deterministic mock provider for unit testing without live API keys."""

    def __init__(self, step_sequence=None):
        super().__init__(api_key="mock_key", model_name="mock-model", timeout_seconds=10)
        self.step_sequence = list(step_sequence or [])
        self.turn = 0
        self.received_messages = []
        self.received_tool_results = []
        self.started_conversations = []

    def start_conversation(self, system_instruction, tool_declarations):
        self.started_conversations.append({
            "system_instruction": system_instruction,
            "tool_declarations": tool_declarations,
        })
        return "mock_session"

    def send_user_message(self, session, message):
        self.received_messages.append(message)
        if self.turn < len(self.step_sequence):
            res = self.step_sequence[self.turn]
            self.turn += 1
            return res
        return ProviderStepResult(is_tool_call=False, text="Default synthesized answer.")

    def send_tool_result(self, session, tool_name, result):
        self.received_tool_results.append((tool_name, result))
        if self.turn < len(self.step_sequence):
            res = self.step_sequence[self.turn]
            self.turn += 1
            return res
        return ProviderStepResult(is_tool_call=False, text="Final answer synthesized from tools.")


# ========================================
# 1. Provider Abstraction Tests
# ========================================

class TestGeminiProvider:
    def test_missing_api_key_raises_configuration_error(self):
        provider = GeminiProvider(api_key="")
        with pytest.raises(ProviderConfigurationError) as exc_info:
            provider.start_conversation(
                system_instruction="test",
                tool_declarations=[],
            )
        assert "API key is not configured" in str(exc_info.value)

    def test_provider_initialization_defaults(self):
        provider = GeminiProvider(api_key="test_key")
        assert provider.model_name in ["gemini-3.8-flash", settings.GEMINI_MODEL]
        assert provider.timeout_seconds == settings.GEMINI_TIMEOUT_SECONDS

    def test_prepare_tool_declarations_formats_types_and_removes_default(self):
        provider = GeminiProvider(api_key="test_key")
        raw_tools = [
            {
                "name": "sample_tool",
                "description": "A sample tool",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lat": {"type": "number", "description": "Latitude", "default": 0.0},
                        "name": {"type": "string", "description": "Name"},
                    },
                    "required": ["lat"],
                },
            }
        ]
        cleaned = provider._prepare_tool_declarations(raw_tools)
        props = cleaned[0]["parameters"]["properties"]
        assert props["lat"]["type"] == "NUMBER"
        assert "default" not in props["lat"]
        assert props["name"]["type"] == "STRING"

    def test_extract_step_result_handles_tool_calls(self):
        provider = GeminiProvider(api_key="test_key")
        mock_response = MagicMock()
        mock_part = MagicMock()
        mock_part.function_call.name = "find_nearest"
        mock_part.function_call.args = {"subcategory": "hospital"}
        mock_part.text = None
        mock_candidate = MagicMock()
        mock_candidate.content.parts = [mock_part]
        mock_response.candidates = [mock_candidate]

        result = provider._extract_step_result(mock_response)
        assert result.is_tool_call is True
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].tool_name == "find_nearest"
        assert result.tool_calls[0].arguments["subcategory"] == "hospital"

    def test_extract_step_result_handles_pure_text(self):
        provider = GeminiProvider(api_key="test_key")
        mock_response = MagicMock()
        mock_part = MagicMock()
        mock_part.function_call = None
        mock_part.text = "Hello developer!"
        mock_candidate = MagicMock()
        mock_candidate.content.parts = [mock_part]
        mock_response.candidates = [mock_candidate]

        result = provider._extract_step_result(mock_response)
        assert result.is_tool_call is False
        assert result.text == "Hello developer!"


# ========================================
# 2. Agent Orchestration Loop Tests
# ========================================

class TestAgentOrchestration:
    @pytest.fixture
    def mock_db_and_user(self):
        db = MagicMock(spec=Session)
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.email = "developer@scapegis.com"
        user.name = "Test Developer"
        user.is_active = True
        return db, user

    @patch("app.spatial_ai.agent.build_spatial_ai_context")
    def test_single_tool_execution_loop(self, mock_build_context, mock_db_and_user):
        db, user = mock_db_and_user
        mock_build_context.return_value = SpatialAIContext(
            user_id=str(user.id),
            user_email=user.email,
            workspace_id=str(FAKE_WORKSPACE_ID),
            workspace_name="Test Workspace",
            authorized_dataset_ids=["ds-1"],
            available_concepts=[],
            available_tools=["find_nearest"],
        )

        # Mock tool output
        mock_tool_output = FindNearestOutput(
            success=True,
            category="public_facility",
            subcategory="hospital",
            target={"latitude": PEKANBARU_LAT, "longitude": PEKANBARU_LNG},
            result=NearestFeatureDetails(
                feature_id="feat-123",
                name="RS Awal Bros",
                distance_m=1250.0,
                distance_km=1.25,
            ),
            source=SpatialProvenance(
                dataset_id="ds-1",
                dataset_name="Pekanbaru GIS",
                layer_id="layer-1",
                layer_name="Rumah Sakit",
                semantic_category="public_facility",
                semantic_subcategory="hospital",
                operation="ST_Distance",
                feature_count_queried=1,
            ),
        )

        mock_registry = MagicMock(spec=SpatialAIToolRegistry)
        mock_registry.to_gemini_declarations.return_value = []
        mock_registry.execute_tool.return_value = mock_tool_output

        # Mock Provider: Turn 1 requests find_nearest, Turn 2 returns final text
        mock_provider = MockAIProvider(step_sequence=[
            ProviderStepResult(
                is_tool_call=True,
                tool_calls=[ToolCallRequest(tool_name="find_nearest", arguments={"subcategory": "hospital"})],
            ),
            ProviderStepResult(
                is_tool_call=False,
                text="Rumah sakit terdekat adalah RS Awal Bros berjarak 1.25 km.",
            ),
        ])

        agent = GeminiSpatialAgent(provider=mock_provider, registry=mock_registry)
        request = SpatialAIAnalysisRequest(
            workspace_id=FAKE_WORKSPACE_ID,
            latitude=PEKANBARU_LAT,
            longitude=PEKANBARU_LNG,
            message="Rumah sakit terdekat?",
        )

        response = agent.analyze(db=db, user=user, request=request)

        assert isinstance(response, SpatialAIResponse)
        assert "RS Awal Bros" in response.answer
        assert len(response.facts) == 1
        assert response.facts[0].type == "distance"
        assert response.facts[0].value == 1250.0
        assert len(response.sources) == 1
        assert response.sources[0].layer_name == "Rumah Sakit"
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0]["tool"] == "find_nearest"

        # Verify MapAction for feature highlight and location marker
        action_types = [a.type for a in response.map_actions]
        assert MapActionType.SHOW_MARKER in action_types
        assert MapActionType.HIGHLIGHT_FEATURE in action_types

    @patch("app.spatial_ai.agent.build_spatial_ai_context")
    def test_multi_tool_execution_loop(self, mock_build_context, mock_db_and_user):
        db, user = mock_db_and_user
        mock_build_context.return_value = SpatialAIContext(
            user_id=str(user.id),
            user_email=user.email,
            workspace_id=str(FAKE_WORKSPACE_ID),
            workspace_name="Multi Test Workspace",
            available_tools=["find_nearest", "search_radius"],
        )

        output_1 = FindNearestOutput(
            success=True,
            category="transportation",
            subcategory="arterial_road",
            target={"latitude": PEKANBARU_LAT, "longitude": PEKANBARU_LNG},
            result=NearestFeatureDetails(
                feature_id="road-1",
                name="Jl. Sudirman",
                distance_m=350.0,
                distance_km=0.35,
            ),
            source=SpatialProvenance(
                dataset_id="ds-1",
                layer_id="layer-road",
                layer_name="Jalan Arteri",
                semantic_category="transportation",
                semantic_subcategory="arterial_road",
                operation="ST_Distance",
            ),
        )

        output_2 = SearchRadiusOutput(
            success=True,
            subcategory="hospital",
            target={"latitude": PEKANBARU_LAT, "longitude": PEKANBARU_LNG},
            radius_m=3000.0,
            count=3,
            features=[
                RadiusFeatureItem(feature_id="h1", name="RS 1", distance_m=1000.0, distance_km=1.0),
                RadiusFeatureItem(feature_id="h2", name="RS 2", distance_m=2000.0, distance_km=2.0),
                RadiusFeatureItem(feature_id="h3", name="RS 3", distance_m=2800.0, distance_km=2.8),
            ],
            sources=[
                SpatialProvenance(
                    dataset_id="ds-1",
                    layer_id="layer-hosp",
                    layer_name="Rumah Sakit",
                    semantic_category="public_facility",
                    semantic_subcategory="hospital",
                    operation="ST_DWithin",
                )
            ],
        )

        mock_registry = MagicMock(spec=SpatialAIToolRegistry)
        mock_registry.to_gemini_declarations.return_value = []
        mock_registry.execute_tool.side_effect = [output_1, output_2]

        # Multi-tool sequence: Turn 1 calls find_nearest, Turn 2 calls search_radius, Turn 3 synthesizes
        mock_provider = MockAIProvider(step_sequence=[
            ProviderStepResult(
                is_tool_call=True,
                tool_calls=[ToolCallRequest(tool_name="find_nearest", arguments={"subcategory": "arterial_road"})],
            ),
            ProviderStepResult(
                is_tool_call=True,
                tool_calls=[ToolCallRequest(tool_name="search_radius", arguments={"subcategory": "hospital", "radius_m": 3000})],
            ),
            ProviderStepResult(
                is_tool_call=False,
                text="Aksesibilitas jalan sangat dekat (350 m) dan ada 3 rumah sakit dalam radius 3 km.",
            ),
        ])

        agent = GeminiSpatialAgent(provider=mock_provider, registry=mock_registry, max_tool_calls=8)
        request = SpatialAIAnalysisRequest(
            workspace_id=FAKE_WORKSPACE_ID,
            latitude=PEKANBARU_LAT,
            longitude=PEKANBARU_LNG,
            message="Bagaimana akses jalan dan fasilitas kesehatan di sekitar?",
        )

        response = agent.analyze(db=db, user=user, request=request)

        assert len(response.facts) == 2
        assert len(response.sources) == 2
        assert len(response.tool_calls) == 2
        assert response.facts[0].type == "distance"
        assert response.facts[1].type == "count"
        assert response.facts[1].value == 3

    @patch("app.spatial_ai.agent.build_spatial_ai_context")
    def test_loop_prevention_enforces_max_tool_calls(self, mock_build_context, mock_db_and_user):
        db, user = mock_db_and_user
        mock_build_context.return_value = SpatialAIContext(
            user_id=str(user.id),
            user_email=user.email,
            workspace_id=str(FAKE_WORKSPACE_ID),
            workspace_name="Loop Test",
            available_tools=["find_nearest"],
        )

        mock_registry = MagicMock(spec=SpatialAIToolRegistry)
        mock_registry.to_gemini_declarations.return_value = []
        mock_registry.execute_tool.return_value = FindNearestOutput(
            success=True, category="test", subcategory="test", target={},
        )

        # Provider that loops indefinitely
        infinite_steps = [
            ProviderStepResult(
                is_tool_call=True,
                tool_calls=[ToolCallRequest(tool_name="find_nearest", arguments={"subcategory": "test"})],
            )
            for _ in range(15)
        ]
        mock_provider = MockAIProvider(step_sequence=infinite_steps)

        max_limit = 3
        agent = GeminiSpatialAgent(provider=mock_provider, registry=mock_registry, max_tool_calls=max_limit)
        request = SpatialAIAnalysisRequest(
            workspace_id=FAKE_WORKSPACE_ID,
            latitude=PEKANBARU_LAT,
            longitude=PEKANBARU_LNG,
            message="Infinite query",
        )

        response = agent.analyze(db=db, user=user, request=request)

        # Iterations must not exceed max_limit
        assert len(response.tool_calls) == max_limit


# ========================================
# 3. Authorization Boundary Tests
# ========================================

class TestAuthorizationBoundary:
    @patch("app.spatial_ai.agent.build_spatial_ai_context")
    def test_unauthorized_workspace_rejected(self, mock_build_context):
        mock_build_context.side_effect = SpatialAIAuthorizationError("User is not a member of this workspace.")

        agent = GeminiSpatialAgent(provider=MockAIProvider())
        request = SpatialAIAnalysisRequest(
            workspace_id=uuid4(),
            latitude=PEKANBARU_LAT,
            longitude=PEKANBARU_LNG,
            message="Test unauth",
        )

        with pytest.raises(SpatialAIAuthorizationError) as exc_info:
            agent.analyze(db=MagicMock(), user=MagicMock(), request=request)
        assert "not a member" in str(exc_info.value)


# ========================================
# 4. API Endpoint Integration Tests
# ========================================

class TestSpatialAIEndpoint:
    def test_endpoint_requires_auth(self):
        client = TestClient(app)
        response = client.post(
            "/api/v1/spatial-ai/analyze",
            json={
                "workspace_id": str(FAKE_WORKSPACE_ID),
                "latitude": PEKANBARU_LAT,
                "longitude": PEKANBARU_LNG,
                "message": "Halo AI",
            },
        )
        # Without auth header, must return 401 Unauthorized
        assert response.status_code == 401

    def test_coordinate_validation_rejects_out_of_bounds(self):
        # Test schema level validation
        with pytest.raises(Exception):
            SpatialAIAnalysisRequest(
                workspace_id=FAKE_WORKSPACE_ID,
                latitude=95.0,  # invalid latitude > 90
                longitude=PEKANBARU_LNG,
                message="Out of bounds",
            )


# ========================================
# 5. Real Gemini Smoke Test (Optional Live)
# ========================================

class TestRealGeminiSmokeTest:
    @pytest.mark.skipif(
        not os.getenv("GEMINI_API_KEY"),
        reason="GEMINI_API_KEY not configured in environment. Skipping live smoke test.",
    )
    def test_real_gemini_roundtrip_find_nearest(self):
        """
        Live smoke test with Google Gemini.
        Validates:
        1. Tool declarations received by Gemini.
        2. Gemini chooses find_nearest for hospital query.
        3. Real synthesis produced without hallucinated facts.
        """
        from app.db.session import SessionLocal

        db = SessionLocal()
        try:
            # Get an active user
            user = db.query(User).filter(User.is_active == True).first()
            if not user:
                pytest.skip("No active user in database to run live test.")

            from app.db.models.workspace_gis_access import WorkspaceGISAccess
            grant = db.query(WorkspaceGISAccess).filter(WorkspaceGISAccess.is_active == True).first()
            if not grant:
                pytest.skip("No workspace GIS grant found.")

            workspace_id = grant.workspace_id

            agent = GeminiSpatialAgent()
            req = SpatialAIAnalysisRequest(
                workspace_id=workspace_id,
                latitude=PEKANBARU_LAT,
                longitude=PEKANBARU_LNG,
                message="Berapa jarak ke rumah sakit terdekat dari lokasi ini?",
            )

            try:
                res = agent.analyze(db=db, user=user, request=req)
                assert res.answer is not None
                assert len(res.answer) > 10
                assert len(res.tool_calls) >= 1
                assert res.tool_calls[0]["tool"] in ["find_nearest", "search_radius", "get_spatial_context"]
                assert len(res.facts) >= 1
                assert len(res.sources) >= 1
                assert len(res.map_actions) >= 1
            except ProviderExecutionError as e:
                if "quota" in str(e).lower() or "rate limit" in str(e).lower() or "exceeded" in str(e).lower():
                    pytest.skip(f"Live Gemini smoke test skipped due to Google API free tier quota limit: {e.message}")
                raise

        finally:
            db.close()
