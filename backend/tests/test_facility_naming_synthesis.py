"""
test_facility_naming_synthesis.py

Verifies honest facility naming in ScapeGIS Spatial AI answers:
- Type labels (REMARK) must never be presented or merged as proper facility names.
- When NAMOBJ is null/empty, facts and tool payloads mark the name as missing
  ("nama tidak tersedia di data") while preserving the type label separately.
- When a proper name exists, it is preserved unchanged.
- The synthesis instruction contains the explicit no-invention and naming rules.
- Mocked agent orchestration respects honest facility naming.
"""
import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.spatial_ai.agent import (
    GeminiSpatialAgent,
    extract_facility_name_and_type,
)
from app.spatial_ai.prompts.system_prompt import (
    BASE_SYSTEM_INSTRUCTION,
    build_spatial_ai_system_instruction,
)
from app.spatial_ai.schemas import (
    FindNearestOutput,
    NearestFeatureDetails,
    SpatialProvenance,
    SpatialAIChatRequest,
)
from app.spatial_ai.providers.base import (
    BaseSpatialAIProvider,
    ProviderStepResult,
    ToolCallRequest,
)
from app.spatial_ai.tool_registry import SpatialAIToolRegistry
from app.spatial_ai.context import SpatialAIContext


class MockNamingProvider(BaseSpatialAIProvider):
    """Mock provider with predictable step progression for testing agent synthesis."""
    model_name = "mock-naming-model"

    def __init__(self, step_sequence):
        self.step_sequence = list(step_sequence)
        self.step_idx = 0
        self.received_tool_results = []

    def start_conversation(self, system_instruction, tool_declarations, history=None):
        return {"instruction": system_instruction, "messages": []}

    def send_user_message(self, session, message):
        res = self.step_sequence[self.step_idx]
        self.step_idx += 1
        return res

    def send_tool_result(self, session, tool_name, result, thought_signature=None):
        self.received_tool_results.append({"tool": tool_name, "result": result})
        res = self.step_sequence[self.step_idx]
        self.step_idx += 1
        return res


# ---------------------------------------------------------------------------
# Test 1: Fact-plumbing test with NAMOBJ null
# ---------------------------------------------------------------------------
def test_fact_plumbing_namobj_null_keeps_type_separate_and_name_missing():
    """
    A tool result with NAMOBJ null produces a fact whose name is marked missing
    ('nama tidak tersedia di data') and whose type label stays separate.
    """
    agent = GeminiSpatialAgent(provider=MagicMock())

    tool_output = FindNearestOutput(
        success=True,
        category="public_facility",
        subcategory="hospital",
        target={"latitude": 0.5071, "longitude": 101.4478},
        result=NearestFeatureDetails(
            feature_id="feat-hosp-null-01",
            name="Rumah Sakit Khusus",
            distance_m=1077.85,
            distance_km=1.078,
            properties={
                "NAMOBJ": None,
                "REMARK": "Rumah Sakit Khusus",
                "ALAMAT": None,
            },
        ),
        source=SpatialProvenance(
            dataset_id=str(uuid4()),
            dataset_name="Kota Pekanbaru",
            layer_id=str(uuid4()),
            layer_name="Dot_LOKASI_RumahSakit",
            semantic_category="public_facility",
            semantic_subcategory="hospital",
            operation="ST_DistanceSphere",
            feature_count_queried=1,
        ),
    )

    # 1. Fact extraction check
    facts, sources, actions = agent._extract_facts_and_provenance("find_nearest", tool_output)
    assert len(facts) == 1
    fact = facts[0]

    # Name is marked missing in the statement
    assert "nama tidak tersedia di data" in fact.statement
    # Type label is present as a type label ('jenis: Rumah Sakit Khusus'), not as a proper name
    assert "jenis: Rumah Sakit Khusus" in fact.statement
    assert "(Rumah Sakit Khusus)" not in fact.statement

    # Map action should have name as None (not the type label)
    assert len(actions) == 1
    assert actions[0].properties.get("name") is None

    # 2. Sanitizer check for LLM tool payload
    sanitized = agent._sanitize_result_for_llm(tool_output)
    res = sanitized["result"]
    assert res["name"] is None
    assert res["name_available"] is False
    assert res["facility_type"] == "Rumah Sakit Khusus"


# ---------------------------------------------------------------------------
# Test 2: Named-path test
# ---------------------------------------------------------------------------
def test_named_path_keeps_proper_name_unchanged():
    """
    A tool result WITH a verified proper name keeps the name unchanged in the fact,
    while keeping the type label separate.
    """
    agent = GeminiSpatialAgent(provider=MagicMock())

    tool_output = FindNearestOutput(
        success=True,
        category="public_facility",
        subcategory="hospital",
        target={"latitude": 0.5071, "longitude": 101.4478},
        result=NearestFeatureDetails(
            feature_id="feat-hosp-named-02",
            name="RS Contoh",
            distance_m=850.0,
            distance_km=0.85,
            properties={
                "NAMOBJ": "RS Contoh",
                "REMARK": "Rumah Sakit Umum",
            },
        ),
        source=SpatialProvenance(
            dataset_id=str(uuid4()),
            layer_id=str(uuid4()),
            layer_name="Dot_LOKASI_RumahSakit",
            semantic_category="public_facility",
            semantic_subcategory="hospital",
            operation="ST_DistanceSphere",
            feature_count_queried=1,
        ),
    )

    # 1. Fact extraction check
    facts, sources, actions = agent._extract_facts_and_provenance("find_nearest", tool_output)
    assert len(facts) == 1
    fact = facts[0]
    assert "(RS Contoh)" in fact.statement
    assert "nama tidak tersedia di data" not in fact.statement

    # Map action preserves the proper name
    assert actions[0].properties.get("name") == "RS Contoh"

    # 2. Sanitizer check
    sanitized = agent._sanitize_result_for_llm(tool_output)
    res = sanitized["result"]
    assert res["name"] == "RS Contoh"
    assert res["name_available"] is True
    assert res["facility_type"] == "Rumah Sakit Umum"


# ---------------------------------------------------------------------------
# Test 3: Synthesis prompt instruction test
# ---------------------------------------------------------------------------
def test_prompt_contains_honest_naming_rule_and_exact_phrase():
    """
    Asserts the synthesis instruction text contains the no-invention rule
    and the exact phrase 'nama tidak tersedia di data'.
    """
    prompt = build_spatial_ai_system_instruction()

    # Exact phrase requirement
    assert "nama tidak tersedia di data" in prompt

    # No invention rule
    assert "never invent, guess, or complete a facility name" in prompt
    assert "Never present a type label as if it were a proper name" in prompt

    # Universal facility coverage
    assert "ALL facility types" in prompt


# ---------------------------------------------------------------------------
# Test 4: Mocked agent run with find_nearest null NAMOBJ
# ---------------------------------------------------------------------------
@patch("app.spatial_ai.agent.build_spatial_ai_context")
def test_mocked_agent_run_honest_naming(mock_build_context):
    """
    find_nearest returns a hospital with NAMOBJ null and REMARK 'Rumah Sakit Khusus'.
    The LLM receives name=None, facility_type='Rumah Sakit Khusus'.
    The composed final response contains 'nama tidak tersedia di data' and does
    not present 'Rumah Sakit Khusus' as a proper hospital name.
    """
    ws_id = uuid4()
    mock_build_context.return_value = SpatialAIContext(
        user_id=str(uuid4()),
        user_email="tester@scapegis.com",
        workspace_id=str(ws_id),
        workspace_name="Honest Naming Workspace",
        available_tools=["find_nearest"],
    )

    mock_registry = MagicMock(spec=SpatialAIToolRegistry)
    mock_registry.to_gemini_declarations.return_value = []
    mock_registry.execute_tool.return_value = FindNearestOutput(
        success=True,
        category="public_facility",
        subcategory="hospital",
        target={"latitude": 0.5071, "longitude": 101.4478},
        result=NearestFeatureDetails(
            feature_id="hosp-001",
            name="Rumah Sakit Khusus",
            distance_m=1077.85,
            distance_km=1.078,
            properties={"NAMOBJ": None, "REMARK": "Rumah Sakit Khusus"},
        ),
        source=SpatialProvenance(
            dataset_id=str(uuid4()),
            layer_id=str(uuid4()),
            layer_name="Dot_LOKASI_RumahSakit",
            semantic_category="public_facility",
            semantic_subcategory="hospital",
            operation="ST_DistanceSphere",
            feature_count_queried=1,
        ),
    )

    steps = [
        ProviderStepResult(
            is_tool_call=True,
            tool_calls=[ToolCallRequest(
                tool_name="find_nearest",
                arguments={"subcategory": "hospital", "latitude": 0.5071, "longitude": 101.4478}
            )],
        ),
        ProviderStepResult(
            is_tool_call=False,
            text="Fasilitas rumah sakit terdekat berjarak 1.078 meter. Jenis fasilitas adalah rumah sakit khusus, namun nama tidak tersedia di data GIS.",
        ),
    ]
    mock_provider = MockNamingProvider(step_sequence=steps)
    agent = GeminiSpatialAgent(provider=mock_provider, registry=mock_registry)

    req = SpatialAIChatRequest(
        workspace_id=ws_id,
        latitude=0.5071,
        longitude=101.4478,
        message="Rumah sakit apa yang paling dekat?",
    )

    res = agent.chat(db=MagicMock(), user=MagicMock(), request=req)

    # Verify tool payload sent to provider has name=None and name_available=False
    assert len(mock_provider.received_tool_results) == 1
    tool_res = mock_provider.received_tool_results[0]["result"]["result"]
    assert tool_res["name"] is None
    assert tool_res["name_available"] is False
    assert tool_res["facility_type"] == "Rumah Sakit Khusus"

    # Verify response
    assert "nama tidak tersedia di data" in res.answer
    assert "nama tidak tersedia di data" in res.facts[0].statement

