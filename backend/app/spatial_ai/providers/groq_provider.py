"""
Groq Spatial AI Provider Implementation

Implements BaseSpatialAIProvider using the official Groq Python SDK.
Enforces local tool calling, single-turn completion per tool invocation,
strict parameter and tool count validation, and safe structured logging.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional

from groq import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    Groq,
    NotFoundError,
    PermissionDeniedError,
)

from app.core.config import settings
from app.spatial_ai.exceptions import (
    MalformedModelResponseError,
    ProviderConfigurationError,
    ProviderExecutionError,
    SpatialAIError,
    ToolLoopExceededError,
)
from app.spatial_ai.providers.base import (
    BaseSpatialAIProvider,
    ProviderStepResult,
    ToolCallRequest,
)

logger = logging.getLogger("app.spatial_ai.providers.groq")

# Gemini to OpenAI type map for recursive tool declaration conversion
GEMINI_TO_OPENAI_TYPE_MAP: Dict[str, str] = {
    "OBJECT": "object",
    "STRING": "string",
    "NUMBER": "number",
    "INTEGER": "integer",
    "BOOLEAN": "boolean",
    "ARRAY": "array",
    "object": "object",
    "string": "string",
    "number": "number",
    "integer": "integer",
    "boolean": "boolean",
    "array": "array",
}


def convert_gemini_schema_to_openai(schema: Any) -> Any:
    """Recursively converts Gemini schema types into standard OpenAI/Groq JSON schema format."""
    if not isinstance(schema, dict):
        return schema

    converted: Dict[str, Any] = {}
    for key, value in schema.items():
        if key == "type" and isinstance(value, str):
            converted["type"] = GEMINI_TO_OPENAI_TYPE_MAP.get(value, value.lower())
        elif key == "properties" and isinstance(value, dict):
            converted["properties"] = {
                prop_name: convert_gemini_schema_to_openai(prop_val)
                for prop_name, prop_val in value.items()
            }
        elif key == "items" and isinstance(value, dict):
            converted["items"] = convert_gemini_schema_to_openai(value)
        else:
            converted[key] = value

    return converted


def convert_gemini_tools_to_groq(tool_declarations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Converts a list of Gemini function declarations into Groq/OpenAI tool format (without strict=true)."""
    groq_tools: List[Dict[str, Any]] = []
    for decl in tool_declarations:
        name = decl.get("name", "")
        desc = decl.get("description", "")
        params = decl.get("parameters") or {}
        converted_params = convert_gemini_schema_to_openai(params)
        if "type" not in converted_params:
            converted_params["type"] = "object"

        groq_tools.append({
            "type": "function",
            "function": {
                "name": name,
                "description": desc,
                "parameters": converted_params,
            },
        })
    return groq_tools


def convert_history_to_groq(history: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Converts conversation history into Groq chat completion messages format.
    - user -> user
    - model / assistant -> assistant
    - parts are merged into content string
    - system roles from history are explicitly rejected / ignored
    """
    if not history:
        return []

    converted: List[Dict[str, Any]] = []
    for item in history:
        raw_role = str(item.get("role", "")).lower()
        if raw_role == "system":
            # Role system dari history ditolak / diabaikan
            continue
        elif raw_role in ("model", "assistant"):
            target_role = "assistant"
        elif raw_role == "user":
            target_role = "user"
        else:
            continue

        if "parts" in item and isinstance(item["parts"], list):
            parts_str: List[str] = []
            for p in item["parts"]:
                if p is None:
                    continue
                if isinstance(p, dict):
                    text_val = p.get("text") or p.get("content") or ""
                    parts_str.append(str(text_val))
                else:
                    parts_str.append(str(p))
            content = "\n".join(parts_str)
        else:
            content = str(item.get("content", ""))

        converted.append({
            "role": target_role,
            "content": content,
        })

    return converted


class GroqSession:
    """Encapsulates active multi-turn conversational state for GroqProvider."""

    def __init__(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        system_instruction: str,
        max_completions: int,
    ):
        self.messages = messages
        self.tools = tools
        self.system_instruction = system_instruction
        self.max_completions = max_completions
        self.completion_count: int = 0
        self.pending_tool_call_id: Optional[str] = None
        self.pending_tool_name: Optional[str] = None


class GroqProvider(BaseSpatialAIProvider):
    """
    Groq implementation of BaseSpatialAIProvider.
    Uses Groq Chat Completions API with local spatial tool calling.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        reasoning_effort: Optional[str] = None,
        max_completion_tokens: Optional[int] = None,
        client: Optional[Groq] = None,
    ):
        key = api_key if api_key is not None else getattr(settings, "GROQ_API_KEY", "")
        model = model_name if model_name is not None else getattr(settings, "GROQ_MODEL", "openai/gpt-oss-120b")
        timeout = timeout_seconds if timeout_seconds is not None else getattr(settings, "GROQ_TIMEOUT_SECONDS", 30)

        super().__init__(api_key=key, model_name=model, timeout_seconds=timeout)

        self.reasoning_effort = (
            reasoning_effort
            if reasoning_effort is not None
            else getattr(settings, "GROQ_REASONING_EFFORT", "medium")
        )
        self.max_completion_tokens = (
            max_completion_tokens
            if max_completion_tokens is not None
            else getattr(settings, "GROQ_MAX_COMPLETION_TOKENS", 1024)
        )

        if not self.api_key or not self.api_key.strip():
            raise ProviderConfigurationError("GROQ_API_KEY is not configured.")

        if client is not None:
            self.client = client
        else:
            self.client = Groq(
                api_key=self.api_key,
                timeout=float(self.timeout_seconds),
                max_retries=0,  # Turn off automatic retries: 1 invocation = 1 HTTP attempt
            )

    def start_conversation(
        self,
        system_instruction: str,
        tool_declarations: List[Dict[str, Any]],
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> GroqSession:
        """Initializes a new conversation session with system instructions and Groq tools."""
        messages: List[Dict[str, Any]] = []

        if system_instruction and system_instruction.strip():
            messages.append({"role": "system", "content": system_instruction.strip()})

        converted_history = convert_history_to_groq(history)
        messages.extend(converted_history)

        converted_tools = convert_gemini_tools_to_groq(tool_declarations)
        max_completions = getattr(settings, "SPATIAL_AI_MAX_TOOL_CALLS", 8) + 1

        return GroqSession(
            messages=messages,
            tools=converted_tools,
            system_instruction=system_instruction,
            max_completions=max_completions,
        )

    def send_user_message(
        self,
        session: GroqSession,
        message: str,
    ) -> ProviderStepResult:
        """Submits a user message and executes the completion turn."""
        if not isinstance(session, GroqSession):
            raise ProviderExecutionError("Invalid session passed to GroqProvider. Expected GroqSession.")

        if session.pending_tool_call_id:
            raise ProviderExecutionError(
                f"Cannot send user message while tool call '{session.pending_tool_name or session.pending_tool_call_id}' is pending."
            )

        session.messages.append({"role": "user", "content": message})
        return self._execute_completion(session, turn_type="user_message")

    def send_tool_result(
        self,
        session: GroqSession,
        tool_name: str,
        result: Dict[str, Any],
        thought_signature: Optional[bytes] = None,
    ) -> ProviderStepResult:
        """
        Feeds back the execution result of a tool.
        Sent as role='tool' message with matched pending tool_call_id,
        JSON-serialized content without 'name' field.
        """
        if not isinstance(session, GroqSession):
            raise ProviderExecutionError("Invalid session passed to GroqProvider. Expected GroqSession.")

        if not session.pending_tool_call_id:
            raise ProviderExecutionError(
                "Cannot return tool result: no pending tool_call_id found in active GroqSession."
            )

        if session.pending_tool_name and tool_name != session.pending_tool_name:
            raise MalformedModelResponseError(
                f"Mismatched tool result: expected '{session.pending_tool_name}', got '{tool_name}'."
            )

        tool_content = json.dumps(result, ensure_ascii=False)
        tool_message = {
            "role": "tool",
            "tool_call_id": session.pending_tool_call_id,
            "content": tool_content,
        }
        session.messages.append(tool_message)
        session.pending_tool_call_id = None
        session.pending_tool_name = None

        return self._execute_completion(session, turn_type="tool_result")

    def _execute_completion(self, session: GroqSession, turn_type: str) -> ProviderStepResult:
        """Dispatches completion request to Groq client and processes response."""
        if session.completion_count >= session.max_completions:
            raise ToolLoopExceededError(
                f"Groq session exceeded maximum completion limit of {session.max_completions}."
            )

        session.completion_count += 1

        create_kwargs: Dict[str, Any] = {
            "model": self.model_name,
            "messages": session.messages,
            "temperature": 0,
            "parallel_tool_calls": False,
        }

        if session.tools:
            create_kwargs["tools"] = session.tools
            create_kwargs["tool_choice"] = "auto"

        if self.reasoning_effort:
            create_kwargs["reasoning_effort"] = self.reasoning_effort

        if self.max_completion_tokens:
            create_kwargs["max_completion_tokens"] = self.max_completion_tokens

        start_time = time.monotonic()
        try:
            raw_response = self.client.chat.completions.with_raw_response.create(**create_kwargs)
            latency = round(time.monotonic() - start_time, 3)
            response = raw_response.parse()
            status_code = raw_response.status_code
            request_id = raw_response.headers.get("x-request-id", "unknown")
        except AuthenticationError as e:
            raise ProviderConfigurationError(
                f"Groq authentication failed (401): {e.message}",
                details={"status_code": 401, "error": str(e)},
            )
        except PermissionDeniedError as e:
            raise ProviderConfigurationError(
                f"Groq permission denied (403): {e.message}",
                details={"status_code": 403, "error": str(e)},
            )
        except NotFoundError as e:
            raise ProviderConfigurationError(
                f"Groq model or resource not found (404): {e.message}",
                details={"status_code": 404, "error": str(e)},
            )
        except APIStatusError as e:
            retry_after = getattr(e.response, "headers", {}).get("retry-after") if hasattr(e, "response") else None
            details: Dict[str, Any] = {
                "status_code": e.status_code,
                "retry_after": retry_after,
                "error": str(e),
            }
            if e.status_code == 413:
                details["payload_too_large"] = True
                raise ProviderExecutionError(
                    f"Groq API error (413): Request payload too large for model. {e.message}",
                    details=details,
                )
            raise ProviderExecutionError(
                f"Groq API error ({e.status_code}): {e.message}",
                details=details,
            )
        except APITimeoutError as e:
            raise ProviderExecutionError(
                f"Groq request timed out after {self.timeout_seconds}s.",
                details={"timeout": self.timeout_seconds, "error": str(e)},
            )
        except APIConnectionError as e:
            raise ProviderExecutionError(
                f"Groq connection error: {str(e)}",
                details={"error": str(e)},
            )
        except Exception as e:
            if isinstance(e, SpatialAIError):
                raise
            raise ProviderExecutionError(
                f"Unexpected error communicating with Groq: {str(e)}",
                details={"error": str(e)},
            )

        # Validate response
        if not response.choices:
            raise MalformedModelResponseError("Groq response contains empty choices list.")

        choice = response.choices[0]
        message = choice.message
        finish_reason = choice.finish_reason or "unknown"
        usage_info = response.usage.model_dump() if response.usage else {}

        # Check for tool calls
        if message.tool_calls:
            if len(message.tool_calls) > 1:
                raise MalformedModelResponseError(
                    f"Groq returned multiple tool calls ({len(message.tool_calls)}); only exactly one tool call is permitted."
                )

            tc = message.tool_calls[0]
            if not tc.function or not tc.function.name:
                raise MalformedModelResponseError("Groq tool call missing function or function name.")

            tool_name = tc.function.name
            raw_args = tc.function.arguments

            try:
                parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                if not isinstance(parsed_args, dict):
                    raise MalformedModelResponseError(
                        f"Groq tool call arguments must parse to a JSON object (dict), got {type(parsed_args).__name__}."
                    )
            except json.JSONDecodeError as err:
                raise MalformedModelResponseError(
                    f"Groq tool call arguments are invalid JSON: {str(err)}."
                )

            # Persist assistant turn in session messages
            session.messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": raw_args,
                        },
                    }
                ],
            })
            session.pending_tool_call_id = tc.id
            session.pending_tool_name = tool_name

            logger.info(
                "Groq completion turn: provider=groq, model=%s, turn_type=%s, messages_count=%d, "
                "tools_count=%d, latency=%.3fs, finish_reason=%s, usage=%s, tool_name=%s, status=%s, request_id=%s",
                self.model_name,
                turn_type,
                len(session.messages),
                len(session.tools),
                latency,
                finish_reason,
                usage_info,
                tool_name,
                status_code,
                request_id,
            )

            return ProviderStepResult(
                text=message.content,
                tool_calls=[
                    ToolCallRequest(
                        tool_name=tool_name,
                        arguments=parsed_args,
                        call_id=tc.id,
                        thought_signature=None,
                    )
                ],
                is_tool_call=True,
                finish_reason=finish_reason,
                metadata={
                    "model": self.model_name,
                    "usage": usage_info,
                    "status_code": status_code,
                    "request_id": request_id,
                    "latency": latency,
                },
            )

        # Text response without tool call
        if message.content is None:
            raise MalformedModelResponseError(
                "Groq completion response contains neither tool_calls nor message content."
            )

        if not message.content.strip():
            raise MalformedModelResponseError(
                "Groq completion response contains empty or whitespace-only message content."
            )

        session.messages.append({
            "role": "assistant",
            "content": message.content,
        })
        session.pending_tool_call_id = None
        session.pending_tool_name = None

        logger.info(
            "Groq completion turn: provider=groq, model=%s, turn_type=%s, messages_count=%d, "
            "tools_count=%d, latency=%.3fs, finish_reason=%s, usage=%s, tool_name=none, status=%s, request_id=%s",
            self.model_name,
            turn_type,
            len(session.messages),
            len(session.tools),
            latency,
            finish_reason,
            usage_info,
            status_code,
            request_id,
        )

        return ProviderStepResult(
            text=message.content,
            tool_calls=[],
            is_tool_call=False,
            finish_reason=finish_reason,
            metadata={
                "model": self.model_name,
                "usage": usage_info,
                "status_code": status_code,
                "request_id": request_id,
                "latency": latency,
            },
        )
