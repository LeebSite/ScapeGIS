"""
Google Gemini Spatial AI Provider

Concrete implementation of BaseSpatialAIProvider utilizing the official
Google Gemini SDK (google-generativeai). Handles tool declarations,
chat sessions, function-calling handshakes, and error handling.
"""
from typing import Dict, Any, List, Optional
import google.generativeai as genai
import google.ai.generativelanguage as glm
from google.api_core.exceptions import GoogleAPICallError, DeadlineExceeded, ResourceExhausted

from app.core.config import settings
from app.spatial_ai.providers.base import (
    BaseSpatialAIProvider,
    ProviderStepResult,
    ToolCallRequest,
)
from app.spatial_ai.exceptions import (
    ProviderConfigurationError,
    ProviderExecutionError,
    MalformedModelResponseError,
)


class GeminiSession:
    """Encapsulates an active Gemini chat session."""
    def __init__(self, chat: Any, model: Any):
        self.chat = chat
        self.model = model


class GeminiProvider(BaseSpatialAIProvider):
    """
    Provider implementation for Google Gemini models.
    Supports multi-turn tool calling with strict ground truth boundaries.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ):
        configured_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        configured_model = model_name if model_name is not None else settings.GEMINI_MODEL
        configured_timeout = (
            timeout_seconds if timeout_seconds is not None else settings.GEMINI_TIMEOUT_SECONDS
        )

        super().__init__(
            api_key=configured_key,
            model_name=configured_model or "gemini-3.8-flash",
            timeout_seconds=configured_timeout or 30,
        )

    def _prepare_tool_declarations(
        self, tool_declarations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Cleans and adapts tool declarations for protobuf Schema compatibility:
        - Ensures type strings are uppercase (STRING, NUMBER, INTEGER, etc.)
        - Removes unsupported fields like 'default'
        """
        cleaned = []
        for decl in tool_declarations:
            copy_decl = {
                "name": decl["name"],
                "description": decl.get("description", ""),
                "parameters": {
                    "type": "OBJECT",
                    "properties": {},
                    "required": decl.get("parameters", {}).get("required", []),
                },
            }
            props = decl.get("parameters", {}).get("properties", {})
            for p_name, p_def in props.items():
                p_type = str(p_def.get("type", "STRING")).upper()
                cleaned_prop = {
                    "type": p_type,
                    "description": p_def.get("description", ""),
                }
                if "enum" in p_def:
                    cleaned_prop["enum"] = p_def["enum"]
                copy_decl["parameters"]["properties"][p_name] = cleaned_prop

            cleaned.append(copy_decl)
        return cleaned

    def start_conversation(
        self,
        system_instruction: str,
        tool_declarations: List[Dict[str, Any]],
    ) -> GeminiSession:
        """Configures Gemini model with tool declarations and primes system instruction."""
        if not self.api_key:
            raise ProviderConfigurationError(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in backend configuration or .env."
            )

        try:
            genai.configure(api_key=self.api_key)
            cleaned_tools = self._prepare_tool_declarations(tool_declarations)

            model = genai.GenerativeModel(
                model_name=self.model_name,
                tools=cleaned_tools if cleaned_tools else None,
            )

            # Prime conversation with system instruction in initial history
            history = [
                {
                    "role": "user",
                    "parts": [f"[SYSTEM INSTRUCTION]\n{system_instruction}"],
                },
                {
                    "role": "model",
                    "parts": [
                        "Understood. I am ScapeGIS Spatial AI. I will analyze questions, invoke spatial tools to obtain ground truth PostGIS facts, and synthesize verified reasoning without hallucinating numbers."
                    ],
                },
            ]

            chat = model.start_chat(
                history=history,
                enable_automatic_function_calling=False,
            )
            return GeminiSession(chat=chat, model=model)

        except Exception as e:
            if isinstance(e, ProviderConfigurationError):
                raise
            raise ProviderExecutionError(
                f"Failed to initialize Gemini session: {str(e)}",
                details={"model": self.model_name, "error": str(e)},
            )

    def _extract_step_result(self, response: Any) -> ProviderStepResult:
        """Extracts tool calls or text response from Gemini response candidate."""
        if not response.candidates:
            raise MalformedModelResponseError("Gemini returned an empty response with no candidates.")

        candidate = response.candidates[0]
        tool_calls: List[ToolCallRequest] = []
        texts: List[str] = []

        for part in candidate.content.parts:
            if hasattr(part, "function_call") and part.function_call:
                fn = part.function_call
                args = {}
                if hasattr(fn, "args") and fn.args:
                    args = dict(fn.args)
                tool_calls.append(
                    ToolCallRequest(
                        tool_name=fn.name,
                        arguments=args,
                    )
                )
            elif hasattr(part, "text") and part.text:
                texts.append(part.text)

        if tool_calls:
            return ProviderStepResult(
                is_tool_call=True,
                tool_calls=tool_calls,
                text="\n".join(texts).strip() if texts else None,
            )

        return ProviderStepResult(
            is_tool_call=False,
            tool_calls=[],
            text="\n".join(texts).strip() if texts else "No response generated.",
        )

    def send_user_message(
        self,
        session: GeminiSession,
        message: str,
    ) -> ProviderStepResult:
        """Sends user message to active Gemini chat session."""
        try:
            response = session.chat.send_message(message)
            return self._extract_step_result(response)
        except DeadlineExceeded as e:
            raise ProviderExecutionError(
                f"Gemini request timed out after {self.timeout_seconds}s.",
                details={"timeout": self.timeout_seconds, "error": str(e)},
            )
        except ResourceExhausted as e:
            raise ProviderExecutionError(
                "Gemini API rate limit or quota exceeded.",
                details={"error": str(e)},
            )
        except GoogleAPICallError as e:
            raise ProviderExecutionError(
                f"Gemini API error: {e.message if hasattr(e, 'message') else str(e)}",
                details={"code": getattr(e, "code", None), "error": str(e)},
            )
        except Exception as e:
            if isinstance(e, (ProviderConfigurationError, ProviderExecutionError, MalformedModelResponseError)):
                raise
            raise ProviderExecutionError(
                f"Unexpected error communicating with Gemini: {str(e)}",
                details={"error": str(e)},
            )

    def send_tool_result(
        self,
        session: GeminiSession,
        tool_name: str,
        result: Dict[str, Any],
    ) -> ProviderStepResult:
        """Feeds tool execution output back to Gemini model as a FunctionResponse."""
        try:
            # Construct protobuf FunctionResponse Part
            part = glm.Part(
                function_response=glm.FunctionResponse(
                    name=tool_name,
                    response={"result": result},
                )
            )
            response = session.chat.send_message(part)
            return self._extract_step_result(response)
        except DeadlineExceeded as e:
            raise ProviderExecutionError(
                f"Gemini request timed out during tool result return ({self.timeout_seconds}s).",
                details={"tool_name": tool_name, "error": str(e)},
            )
        except ResourceExhausted as e:
            raise ProviderExecutionError(
                "Gemini API quota exceeded during tool feedback.",
                details={"tool_name": tool_name, "error": str(e)},
            )
        except GoogleAPICallError as e:
            raise ProviderExecutionError(
                f"Gemini API error during tool feedback: {str(e)}",
                details={"tool_name": tool_name, "error": str(e)},
            )
        except Exception as e:
            if isinstance(e, (ProviderConfigurationError, ProviderExecutionError, MalformedModelResponseError)):
                raise
            raise ProviderExecutionError(
                f"Unexpected error sending tool result to Gemini: {str(e)}",
                details={"tool_name": tool_name, "error": str(e)},
            )
