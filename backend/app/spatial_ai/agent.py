"""
Gemini Spatial Reasoning Agent

Orchestrates multi-turn spatial reasoning between the property developer,
Google Gemini, and the ScapeGIS PostGIS Tool Registry.
Enforces multi-tenant authorization, ground-truth fact extraction,
provenance tracking, map action derivation, and loop prevention.
"""
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.user import User
from app.spatial_ai.context import build_spatial_ai_context, SpatialAIContext
from app.spatial_ai.prompts.system_prompt import build_spatial_ai_system_instruction
from app.spatial_ai.providers.base import BaseSpatialAIProvider
from app.spatial_ai.providers.gemini_provider import GeminiProvider
from app.spatial_ai.tool_registry import SpatialAIToolRegistry, default_registry
import re
from app.spatial_ai.schemas import (
    SpatialAIAnalysisRequest,
    SpatialAIChatRequest,
    ChatMessage,
    ChatMessageRole,
    SpatialAIResponse,
    SpatialFact,
    SpatialProvenance,
    MapAction,
    MapActionType,
    FindNearestOutput,
    SearchRadiusOutput,
    CheckContainmentOutput,
    FindIntersectionsOutput,
    GetSpatialContextOutput,
)
from app.spatial_ai.exceptions import (
    SpatialAIError,
    SpatialAIAuthorizationError,
    ToolLoopExceededError,
    ProviderExecutionError,
)


class GeminiSpatialAgent:
    """
    Core AI reasoning agent for ScapeGIS.
    Executes controlled tool calling cycles and synthesizes responses
    strictly from PostGIS ground-truth facts.
    """

    def __init__(
        self,
        provider: Optional[BaseSpatialAIProvider] = None,
        registry: Optional[SpatialAIToolRegistry] = None,
        max_tool_calls: Optional[int] = None,
    ):
        self.provider = provider or GeminiProvider()
        self.registry = registry or default_registry
        self.max_tool_calls = (
            max_tool_calls
            if max_tool_calls is not None
            else settings.SPATIAL_AI_MAX_TOOL_CALLS
        )

    def analyze(
        self,
        db: Session,
        user: User,
        request: SpatialAIAnalysisRequest,
    ) -> SpatialAIResponse:
        """
        Executes the spatial AI reasoning pipeline:
        1. Builds & validates SpatialAIContext (tenant authorization).
        2. Primes system instruction & Gemini tool declarations.
        3. Executes tool calling orchestration loop.
        4. Synthesizes facts, provenance, and map actions into SpatialAIResponse.
        """
        context = build_spatial_ai_context(
            db=db,
            user=user,
            workspace_id=request.workspace_id,
            project_id=request.project_id,
        )

        user_prompt = (
            f"Target Location: Latitude {request.latitude}, Longitude {request.longitude}.\n"
            f"Workspace ID: {request.workspace_id}\n"
        )
        if request.project_id:
            user_prompt += f"Project ID: {request.project_id}\n"
        user_prompt += f"\nUser Question:\n{request.message}"

        coords = (request.latitude, request.longitude)

        return self._run_orchestration_loop(
            db=db,
            user=user,
            context=context,
            user_prompt=user_prompt,
            workspace_id=request.workspace_id,
            project_id=request.project_id,
            coords=coords,
            history=None,
        )

    def chat(
        self,
        db: Session,
        user: User,
        request: SpatialAIChatRequest,
    ) -> SpatialAIResponse:
        """
        Executes the multi-turn spatial AI chat pipeline (Module 2C):
        1. Builds & validates SpatialAIContext (tenant authorization).
        2. Sanitizes and bounds conversation history.
        3. Reuses controlled PostGIS tool contracts and loop limits.
        4. Synthesizes structured response with facts, provenance, and map actions.
        """
        context = build_spatial_ai_context(
            db=db,
            user=user,
            workspace_id=request.workspace_id,
            project_id=request.project_id,
        )

        user_prompt = f"Workspace ID: {request.workspace_id}\n"
        if request.project_id:
            user_prompt += f"Project ID: {request.project_id}\n"
        if request.latitude is not None and request.longitude is not None:
            user_prompt += f"Target Location: Latitude {request.latitude}, Longitude {request.longitude}.\n"
        user_prompt += f"\nUser Question:\n{request.message}"

        coords = (
            (request.latitude, request.longitude)
            if request.latitude is not None and request.longitude is not None
            else None
        )
        sanitized_history = self._prepare_and_sanitize_history(request.history)

        return self._run_orchestration_loop(
            db=db,
            user=user,
            context=context,
            user_prompt=user_prompt,
            workspace_id=request.workspace_id,
            project_id=request.project_id,
            coords=coords,
            history=sanitized_history,
        )

    def _prepare_and_sanitize_history(
        self,
        history: List[ChatMessage],
    ) -> List[Dict[str, Any]]:
        """
        Validates, bounds, and sanitizes user-supplied conversation history:
        - Bounded to settings.SPATIAL_AI_MAX_HISTORY_MESSAGES.
        - Maps ChatMessageRole to provider roles ('user' -> 'user', 'assistant' -> 'model').
        - Neutralizes deceptive system instruction headers.
        """
        if not history:
            return []

        max_messages = getattr(settings, "SPATIAL_AI_MAX_HISTORY_MESSAGES", 10)
        bounded = history[-max_messages:]

        sanitized_turns: List[Dict[str, Any]] = []
        for msg in bounded:
            role = "user" if msg.role == ChatMessageRole.USER else "model"
            content = msg.content or ""
            # Neutralize potential prompt injection mimicking system prompt headers
            neutralized_content = re.sub(
                r"\[\s*SYSTEM(?:\s+INSTRUCTION)?\s*\]",
                "[PREVIOUS_CONTEXT]",
                content,
                flags=re.IGNORECASE,
            )
            sanitized_turns.append({
                "role": role,
                "parts": [neutralized_content],
            })

        return sanitized_turns

    def _run_orchestration_loop(
        self,
        db: Session,
        user: User,
        context: SpatialAIContext,
        user_prompt: str,
        workspace_id: UUID,
        project_id: Optional[UUID],
        coords: Optional[Tuple[float, float]],
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> SpatialAIResponse:
        """
        Shared reasoning and tool execution loop between single-turn analysis
        and multi-turn chat sessions.
        """
        system_instruction = build_spatial_ai_system_instruction(context)
        tool_declarations = self.registry.to_gemini_declarations()

        session = self.provider.start_conversation(
            system_instruction=system_instruction,
            tool_declarations=tool_declarations,
            history=history,
        )

        step = self.provider.send_user_message(session, user_prompt)

        accumulated_facts: List[SpatialFact] = []
        accumulated_sources: List[SpatialProvenance] = []
        accumulated_map_actions: List[MapAction] = []
        tool_calls_trace: List[Dict[str, Any]] = []

        if coords:
            accumulated_map_actions.append(
                MapAction(
                    type=MapActionType.SHOW_MARKER,
                    coordinates={"latitude": coords[0], "longitude": coords[1]},
                    properties={"title": "Lokasi Target Analisis"},
                )
            )

        iteration = 0
        while step.is_tool_call and step.tool_calls:
            if iteration >= self.max_tool_calls:
                break

            for call in step.tool_calls:
                iteration += 1
                if iteration > self.max_tool_calls:
                    break

                tool_name = call.tool_name
                raw_args = dict(call.arguments)

                # Security: ALWAYS enforce backend-provided tenant scope and coordinates
                raw_args["workspace_id"] = str(workspace_id)
                if project_id:
                    raw_args["project_id"] = str(project_id)
                elif "project_id" in raw_args:
                    del raw_args["project_id"]
                if coords:
                    if "latitude" not in raw_args:
                        raw_args["latitude"] = coords[0]
                    if "longitude" not in raw_args:
                        raw_args["longitude"] = coords[1]

                # Execute controlled tool via registry
                try:
                    tool_output = self.registry.execute_tool(
                        name=tool_name,
                        db=db,
                        user=user,
                        params=raw_args,
                    )

                    facts, sources, actions = self._extract_facts_and_provenance(
                        tool_name=tool_name,
                        tool_output=tool_output,
                    )
                    accumulated_facts.extend(facts)
                    accumulated_sources.extend(sources)
                    accumulated_map_actions.extend(actions)

                    tool_calls_trace.append({
                        "iteration": iteration,
                        "tool": tool_name,
                        "arguments": raw_args,
                        "success": True,
                    })

                    safe_result = self._sanitize_result_for_llm(tool_output)

                except Exception as e:
                    tool_calls_trace.append({
                        "iteration": iteration,
                        "tool": tool_name,
                        "arguments": raw_args,
                        "success": False,
                        "error": str(e),
                    })
                    safe_result = {
                        "tool": tool_name,
                        "success": False,
                        "error": str(e),
                    }

                step = self.provider.send_tool_result(
                    session=session,
                    tool_name=tool_name,
                    result=safe_result,
                )

        final_answer = step.text or (
            "Analisis spasial berhasil dieksekusi berdasarkan layer GIS yang tersedia di workspace Anda."
        )

        return SpatialAIResponse(
            answer=final_answer,
            facts=accumulated_facts,
            sources=self._deduplicate_sources(accumulated_sources),
            map_actions=self._deduplicate_map_actions(accumulated_map_actions),
            tool_calls=tool_calls_trace,
            model=self.provider.model_name,
        )

    def _extract_facts_and_provenance(
        self,
        tool_name: str,
        tool_output: Any,
    ) -> Tuple[List[SpatialFact], List[SpatialProvenance], List[MapAction]]:
        """Extracts atomic facts, provenance sources, and map actions from tool output."""
        facts: List[SpatialFact] = []
        sources: List[SpatialProvenance] = []
        actions: List[MapAction] = []

        if isinstance(tool_output, FindNearestOutput) and tool_output.success:
            if tool_output.source:
                sources.append(tool_output.source)
            if tool_output.result:
                name_str = f" ({tool_output.result.name})" if tool_output.result.name else ""
                facts.append(
                    SpatialFact(
                        type="distance",
                        category=tool_output.category,
                        subcategory=tool_output.subcategory,
                        statement=f"Fasilitas {tool_output.subcategory} terdekat{name_str} berjarak {tool_output.result.distance_km} km ({tool_output.result.distance_m} meter).",
                        value=tool_output.result.distance_m,
                        unit="meter",
                        source_layer=tool_output.source.layer_name if tool_output.source else None,
                        dataset_id=tool_output.source.dataset_id if tool_output.source else None,
                    )
                )
                if tool_output.source and tool_output.result.feature_id:
                    actions.append(
                        MapAction(
                            type=MapActionType.HIGHLIGHT_FEATURE,
                            layer_id=tool_output.source.layer_id,
                            feature_ids=[tool_output.result.feature_id],
                            properties={"name": tool_output.result.name, "distance_m": tool_output.result.distance_m},
                        )
                    )

        elif isinstance(tool_output, SearchRadiusOutput) and tool_output.success:
            sources.extend(tool_output.sources)
            facts.append(
                SpatialFact(
                    type="count",
                    category="spatial_analysis",
                    subcategory=tool_output.subcategory,
                    statement=f"Ditemukan {tool_output.count} fasilitas {tool_output.subcategory} dalam radius {int(tool_output.radius_m)} meter.",
                    value=tool_output.count,
                    unit="unit",
                )
            )
            feat_ids = [f.feature_id for f in tool_output.features if f.feature_id]
            if feat_ids and tool_output.sources:
                actions.append(
                    MapAction(
                        type=MapActionType.HIGHLIGHT_FEATURE,
                        layer_id=tool_output.sources[0].layer_id,
                        feature_ids=feat_ids[:15],
                    )
                )

        elif isinstance(tool_output, CheckContainmentOutput) and tool_output.success:
            if tool_output.source:
                sources.append(tool_output.source)
            if tool_output.contained:
                facts.append(
                    SpatialFact(
                        type="containment",
                        category=tool_output.source.semantic_category if tool_output.source else "administrative",
                        subcategory=tool_output.source.semantic_subcategory if tool_output.source else "boundary",
                        statement=f"Lokasi berada dalam wilayah batas administratif: {tool_output.area_name}.",
                        value=tool_output.area_name or "Contained",
                        unit="area",
                        source_layer=tool_output.source.layer_name if tool_output.source else None,
                        dataset_id=tool_output.source.dataset_id if tool_output.source else None,
                    )
                )
                if tool_output.source and tool_output.feature_id:
                    actions.append(
                        MapAction(
                            type=MapActionType.HIGHLIGHT_FEATURE,
                            layer_id=tool_output.source.layer_id,
                            feature_ids=[str(tool_output.feature_id)],
                        )
                    )
            else:
                facts.append(
                    SpatialFact(
                        type="containment",
                        category="administrative",
                        subcategory="boundary",
                        statement="Koordinat berada di luar poligon wilayah administratif yang terdata.",
                        value="Outside",
                        unit="area",
                    )
                )

        elif isinstance(tool_output, FindIntersectionsOutput) and tool_output.success:
            sources.extend(tool_output.sources)
            facts.append(
                SpatialFact(
                    type="accessibility",
                    category="transportation",
                    subcategory="road",
                    statement=f"Ditemukan {tool_output.count} segmen fitur jaringan jalan berpotongan dalam buffer {int(tool_output.buffer_m)} meter.",
                    value=tool_output.count,
                    unit="unit",
                )
            )

        elif isinstance(tool_output, GetSpatialContextOutput) and tool_output.success:
            sources.extend(tool_output.sources)
            for f_dict in tool_output.facts:
                facts.append(
                    SpatialFact(
                        type=f_dict.get("type", "context"),
                        category=f_dict.get("domain", "general"),
                        subcategory=f_dict.get("item", "context"),
                        statement=f_dict.get("statement", ""),
                        value=f_dict.get("value", 0),
                        unit=f_dict.get("unit"),
                    )
                )

        return facts, sources, actions

    def _sanitize_result_for_llm(self, tool_output: Any) -> Dict[str, Any]:
        """
        Strips heavy raw geometry and produces compact, safe JSON dictionary
        for LLM prompt reasoning.
        """
        if hasattr(tool_output, "model_dump"):
            d = tool_output.model_dump()
        elif isinstance(tool_output, dict):
            d = dict(tool_output)
        else:
            return {"output": str(tool_output)}

        # Filter out bulky geometry strings or excessive nested arrays
        if "features" in d and isinstance(d["features"], list):
            # Limit features passed into LLM prompt
            d["features"] = d["features"][:10]
            for f in d["features"]:
                if isinstance(f, dict):
                    f.pop("geometry", None)
                    f.pop("geojson", None)

        return d

    def _deduplicate_sources(self, sources: List[SpatialProvenance]) -> List[SpatialProvenance]:
        """Deduplicates provenance entries by layer_id and operation."""
        seen = set()
        deduped = []
        for s in sources:
            key = (s.layer_id, s.operation)
            if key not in seen:
                seen.add(key)
                deduped.append(s)
        return deduped

    def _deduplicate_map_actions(self, actions: List[MapAction]) -> List[MapAction]:
        """Deduplicates map actions."""
        seen = set()
        deduped = []
        for a in actions:
            key = (a.type, a.layer_id, tuple(a.feature_ids or []))
            if key not in seen:
                seen.add(key)
                deduped.append(a)
        return deduped
