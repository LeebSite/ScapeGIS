"""
ScapeGIS GL-03 Acceptance Test Suite

Mapping Design-Test-ID to Implementation-Test-ID:
1. GL03-TOOL-01 -> test_gl03_tool_01_find_nearest
2. GL03-TOOL-02 -> test_gl03_tool_02_search_radius
3. GL03-TOOL-03 -> test_gl03_tool_03_check_containment
4. GL03-TOOL-04 -> test_gl03_tool_04_find_intersections
5. GL03-TOOL-05 -> test_gl03_tool_05_get_spatial_context
6. GL03-SEC-01  -> test_gl03_sec_01_tenant_authorization_protection
7. GL03-SEC-02  -> test_gl03_sec_02_project_scoping_enforcement
8. GL03-VAL-01  -> test_gl03_val_01_bounded_search_zero_result
9. GL03-CHAT-01 -> test_gl03_chat_01_multi_turn_conversational_history
"""
import json
from types import SimpleNamespace
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.db.session import SessionLocal
from app.db.models.user import User
from app.core.security import create_access_token
from app.spatial_ai.agent import GeminiSpatialAgent
from app.spatial_ai.schemas import (
    SpatialAIChatRequest,
    ChatMessage,
    ChatMessageRole,
    FindNearestOutput,
    SearchRadiusOutput,
    CheckContainmentOutput,
    FindIntersectionsOutput,
    GetSpatialContextOutput,
    NearestFeatureDetails,
    SpatialProvenance,
)
from app.spatial_ai.providers.groq_provider import GroqProvider
from app.spatial_ai.tool_registry import create_default_registry
from groq.types.chat.chat_completion import ChatCompletion


def make_sdk_completion(
    content: Optional[str] = None,
    tool_calls: Optional[List[Dict[str, Any]]] = None,
    finish_reason: str = "stop",
) -> ChatCompletion:
    msg: Dict[str, Any] = {"role": "assistant", "content": content}
    if tool_calls is not None:
        msg["tool_calls"] = tool_calls
    return ChatCompletion.model_validate({
        "id": "chatcmpl-gl03-fixture",
        "choices": [{"finish_reason": finish_reason, "index": 0, "message": msg}],
        "created": 1700000000,
        "model": "openai/gpt-oss-120b",
        "object": "chat.completion",
        "usage": {"completion_tokens": 50, "prompt_tokens": 100, "total_tokens": 150},
    })


def make_raw_resp(completion: ChatCompletion, status_code: int = 200):
    return SimpleNamespace(
        parse=lambda: completion,
        status_code=status_code,
        headers={"x-request-id": "req-gl03-test"},
    )


WORKSPACE_ID = "2a12cd6e-3644-4f72-989b-ac7737d06e3a"
PROJECT_ID = "86d49543-f049-4060-a6b1-bb0bbde88ec9"
LAT, LON = 0.5071, 101.4478


# ---------------------------------------------------------------------------
# GL03-TOOL-01: find_nearest
# ---------------------------------------------------------------------------
def test_gl03_tool_01_find_nearest():
    """GL03-TOOL-01: find_nearest identifies nearest hospital at 1077.85m."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "ghalibpradipaa04@gmail.com").first()
        registry = create_default_registry()
        res = registry.execute_tool(
            "find_nearest",
            db,
            user,
            {"workspace_id": WORKSPACE_ID, "latitude": LAT, "longitude": LON, "subcategory": "hospital"}
        )
        assert res.success is True
        assert res.result.name == "Rumah Sakit Khusus"
        assert abs(res.result.distance_m - 1077.85) < 0.1
        assert res.source.layer_name == "Dot_LOKASI_RumahSakit"
    finally:
        db.close()


# ---------------------------------------------------------------------------
# GL03-TOOL-02: search_radius
# ---------------------------------------------------------------------------
def test_gl03_tool_02_search_radius():
    """GL03-TOOL-02: search_radius finds 2 mosques within 1000m radius."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "ghalibpradipaa04@gmail.com").first()
        registry = create_default_registry()
        res = registry.execute_tool(
            "search_radius",
            db,
            user,
            {"workspace_id": WORKSPACE_ID, "latitude": LAT, "longitude": LON, "subcategory": "mosque", "radius_m": 1000.0}
        )
        assert res.success is True
        assert res.count == 2
        assert len(res.features) == 2
        assert res.sources[0].dataset_name == "Kota Pekanbaru"
    finally:
        db.close()


# ---------------------------------------------------------------------------
# GL03-TOOL-03: check_containment
# ---------------------------------------------------------------------------
def test_gl03_tool_03_check_containment():
    """GL03-TOOL-03: check_containment confirms containment in MARPOYANDAMAI boundary."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "ghalibpradipaa04@gmail.com").first()
        registry = create_default_registry()
        res = registry.execute_tool(
            "check_containment",
            db,
            user,
            {"workspace_id": WORKSPACE_ID, "latitude": LAT, "longitude": LON, "subcategory": "administrative_boundary"}
        )
        assert res.success is True
        assert res.contained is True
        assert res.area_name == "MARPOYANDAMAI"
        assert res.source.operation == "ST_Contains"
    finally:
        db.close()


# ---------------------------------------------------------------------------
# GL03-TOOL-04: find_intersections
# ---------------------------------------------------------------------------
def test_gl03_tool_04_find_intersections():
    """GL03-TOOL-04: find_intersections detects arterial road intersections within 500m buffer."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "ghalibpradipaa04@gmail.com").first()
        registry = create_default_registry()
        res = registry.execute_tool(
            "find_intersections",
            db,
            user,
            {"workspace_id": WORKSPACE_ID, "latitude": LAT, "longitude": LON, "subcategory": "arterial_road", "buffer_m": 500.0}
        )
        assert res.success is True
        assert res.count == 2
        assert abs(res.features[0]["distance_meters"] - 303.18) < 0.1
        assert res.sources[0].layer_name == "Dot_LINE_JalanArteri"
    finally:
        db.close()


# ---------------------------------------------------------------------------
# GL03-TOOL-05: get_spatial_context
# ---------------------------------------------------------------------------
def test_gl03_tool_05_get_spatial_context():
    """GL03-TOOL-05: get_spatial_context aggregates intelligence profile across GIS layers."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "ghalibpradipaa04@gmail.com").first()
        registry = create_default_registry()
        res = registry.execute_tool(
            "get_spatial_context",
            db,
            user,
            {"workspace_id": WORKSPACE_ID, "latitude": LAT, "longitude": LON}
        )
        assert res.success is True
        assert len(res.facts) > 0
        assert len(res.sources) > 0
    finally:
        db.close()


# ---------------------------------------------------------------------------
# GL03-SEC-01: Tenant Authorization Protection
# ---------------------------------------------------------------------------
def test_gl03_sec_01_tenant_authorization_protection():
    """GL03-SEC-01: Non-member user access returns HTTP 403 Forbidden."""
    db = SessionLocal()
    try:
        non_member = db.query(User).filter(User.email == "lezatin.idfood@gmail.com").first()
        token = create_access_token(data={"sub": str(non_member.id)})
    finally:
        db.close()

    client = TestClient(app)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "message": "Cari rumah sakit terdekat.",
        "workspace_id": WORKSPACE_ID,
        "latitude": LAT,
        "longitude": LON,
    }
    resp = client.post("/api/v1/spatial-ai/chat", headers=headers, json=payload)
    assert resp.status_code == 403
    assert "Access forbidden" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# GL03-SEC-02: Project Scoping Enforcement
# ---------------------------------------------------------------------------
def test_gl03_sec_02_project_scoping_enforcement():
    """GL03-SEC-02: User-supplied project_id is strictly bound and scoped in tool arguments."""
    mock_client = MagicMock()
    tc = [{
        "id": "call_proj_scope",
        "type": "function",
        "function": {
            "name": "find_nearest",
            "arguments": '{"latitude": 0.5071, "longitude": 101.4478, "subcategory": "hospital"}',
        },
    }]
    compl_1 = make_sdk_completion(content=None, tool_calls=tc, finish_reason="tool_calls")
    compl_2 = make_sdk_completion(content="RS Khusus berjarak 1077.85m.", finish_reason="stop")
    mock_client.chat.completions.with_raw_response.create.side_effect = [
        make_raw_resp(compl_1),
        make_raw_resp(compl_2),
    ]

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "ghalibpradipaa04@gmail.com").first()
        groq_prov = GroqProvider(api_key="gsk_test_key", client=mock_client)
        agent = GeminiSpatialAgent(provider=groq_prov)

        req = SpatialAIChatRequest(
            workspace_id=UUID(WORKSPACE_ID),
            project_id=UUID(PROJECT_ID),
            latitude=LAT,
            longitude=LON,
            message="Cari RS terdekat untuk proyek.",
        )
        response = agent.chat(db=db, user=user, request=req)

        assert len(response.tool_calls) == 1
        tc_args = response.tool_calls[0]["arguments"]
        assert tc_args["project_id"] == PROJECT_ID
        assert tc_args["workspace_id"] == WORKSPACE_ID
    finally:
        db.close()


# ---------------------------------------------------------------------------
# GL03-VAL-01: Bounded Search / Zero Result Graceful Handling
# ---------------------------------------------------------------------------
def test_gl03_val_01_bounded_search_zero_result():
    """GL03-VAL-01: Query returning zero features handles response gracefully without failure."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "ghalibpradipaa04@gmail.com").first()
        registry = create_default_registry()
        # Search port within 100m -> port is in Pelabuhan Sungai Duku, kilometers away
        res = registry.execute_tool(
            "search_radius",
            db,
            user,
            {"workspace_id": WORKSPACE_ID, "latitude": LAT, "longitude": LON, "subcategory": "port", "radius_m": 100.0}
        )
        assert res.success is True
        assert res.count == 0
        assert len(res.features) == 0
    finally:
        db.close()


# ---------------------------------------------------------------------------
# GL03-CHAT-01: Multi-Turn Conversational History
# ---------------------------------------------------------------------------
def test_gl03_chat_01_multi_turn_conversational_history():
    """GL03-CHAT-01: History is converted, injected, and used in reasoning without re-invoking tools."""
    mock_client = MagicMock()
    # In follow-up, model answers directly from context without calling tool
    compl = make_sdk_completion(content="Waktu tempuh sekitar 12-15 menit berjalan kaki.", finish_reason="stop")
    mock_client.chat.completions.with_raw_response.create.return_value = make_raw_resp(compl)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "ghalibpradipaa04@gmail.com").first()
        groq_prov = GroqProvider(api_key="gsk_test_key", client=mock_client)
        agent = GeminiSpatialAgent(provider=groq_prov)

        req = SpatialAIChatRequest(
            workspace_id=UUID(WORKSPACE_ID),
            latitude=LAT,
            longitude=LON,
            message="Berapa menit jika berjalan kaki?",
            history=[
                ChatMessage(role=ChatMessageRole.USER, content="Di mana RS terdekat?"),
                ChatMessage(role=ChatMessageRole.ASSISTANT, content="Rumah sakit terdekat adalah Rumah Sakit Khusus berjarak 1077.85m."),
            ],
        )
        response = agent.chat(db=db, user=user, request=req)

        assert len(response.tool_calls) == 0
        assert "12-15 menit" in response.answer

        # Verify history passed to Groq client
        create_kwargs = mock_client.chat.completions.with_raw_response.create.call_args.kwargs
        messages = create_kwargs["messages"]
        # messages: [system, user (hist), assistant (hist), user (current)]
        assert len(messages) == 5
        assert messages[4]["role"] == "assistant"
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"
        assert messages[3]["role"] == "user"
    finally:
        db.close()
