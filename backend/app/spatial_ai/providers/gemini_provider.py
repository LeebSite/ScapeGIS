"""
Google Gemini Spatial AI Provider

Concrete implementation of BaseSpatialAIProvider utilizing the official
Google GenAI SDK (google-genai). Handles tool declarations,
chat sessions, function-calling handshakes, and error handling.
"""
from typing import Dict, Any, List, Optional
import httpx
from google import genai
from google.genai import types, errors

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
    def __init__(self, chat: Any, model: Any = None, client: Any = None):
        self.chat = chat
        self.model = model
        self.client = client


class GeminiProvider(BaseSpatialAIProvider):
    """
    Provider implementation for Google Gemini models using the official google-genai SDK.
    Supports multi-turn tool calling with strict ground truth boundaries and thought_signature.
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
    ) -> List[types.FunctionDeclaration]:
        """
        Adapts tool declarations for google-genai FunctionDeclaration:
        - Ensures parameter types are Schema compatible
        - Strips 'default' attributes for strict schema conformity
        """
        declarations = []
        for decl in tool_declarations:
            copy_params = dict(decl.get("parameters", {}))
            props = dict(copy_params.get("properties", {}))
            cleaned_props = {}
            for p_name, p_def in props.items():
                p_copy = dict(p_def)
                if "type" in p_copy:
                    p_copy["type"] = str(p_copy["type"]).upper()
                p_copy.pop("default", None)
                cleaned_props[p_name] = p_copy
            copy_params["properties"] = cleaned_props
            declarations.append(
                types.FunctionDeclaration(
                    name=decl["name"],
                    description=decl.get("description", ""),
                    parameters=copy_params,
                )
            )
        return declarations

    def start_conversation(
        self,
        system_instruction: str,
        tool_declarations: List[Dict[str, Any]],
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> GeminiSession:
        """Configures Gemini model with tool declarations, system instruction, and appends prior history."""
        if not self.api_key:
            raise ProviderConfigurationError(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in backend configuration or .env."
            )

        try:
            client = genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(timeout=int(self.timeout_seconds * 1000)),
            )

            tools = None
            if tool_declarations:
                fds = self._prepare_tool_declarations(tool_declarations)
                tools = [types.Tool(function_declarations=fds)]

            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=tools,
            )

            contents_history: Optional[List[types.Content]] = None
            if history:
                contents_history = []
                for turn in history:
                    role_raw = turn.get("role", "user")
                    role = "model" if role_raw in ("model", "assistant") else "user"
                    parts = []
                    for p in turn.get("parts", []):
                        if isinstance(p, types.Part):
                            parts.append(p)
                        elif isinstance(p, str):
                            parts.append(types.Part.from_text(text=p))
                        elif isinstance(p, dict):
                            if "text" in p:
                                parts.append(types.Part.from_text(text=p["text"]))
                            else:
                                parts.append(types.Part.model_validate(p))
                        else:
                            parts.append(types.Part.from_text(text=str(p)))
                    contents_history.append(types.Content(role=role, parts=parts))

            chat = client.chats.create(
                model=self.model_name,
                config=config,
                history=contents_history,
            )
            return GeminiSession(chat=chat, model=self.model_name, client=client)

        except Exception as e:
            if isinstance(e, ProviderConfigurationError):
                raise
            raise ProviderExecutionError(
                f"Failed to initialize Gemini session: {str(e)}",
                details={"model": self.model_name, "error": str(e)},
            )

    def _extract_step_result(self, response: Any) -> ProviderStepResult:
        """Extracts tool calls or text response from Gemini response candidate."""
        if not response or not getattr(response, "candidates", None):
            raise MalformedModelResponseError("Gemini returned an empty response with no candidates.")

        candidate = response.candidates[0]
        if not getattr(candidate, "content", None) or not getattr(candidate.content, "parts", None):
            return ProviderStepResult(
                is_tool_call=False,
                tool_calls=[],
                text="No response generated.",
            )

        tool_calls: List[ToolCallRequest] = []
        texts: List[str] = []

        for part in candidate.content.parts:
            if hasattr(part, "function_call") and part.function_call:
                fn = part.function_call
                args = {}
                if hasattr(fn, "args") and fn.args:
                    args = dict(fn.args)
                
                # Take thought_signature from Part (part.thought_signature), NOT from FunctionCall
                thought_sig = getattr(part, "thought_signature", None)
                if isinstance(thought_sig, (bytes, bytearray)):
                    thought_sig = bytes(thought_sig)
                elif isinstance(thought_sig, str):
                    thought_sig = thought_sig.encode("utf-8")
                else:
                    thought_sig = None

                tool_calls.append(
                    ToolCallRequest(
                        tool_name=fn.name,
                        arguments=args,
                        thought_signature=thought_sig,
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
        except errors.APIError as e:
            if getattr(e, "code", None) == 429 or "quota" in str(e).lower() or "resource_exhausted" in str(e).lower():
                raise ProviderExecutionError(
                    "Gemini API rate limit or quota exceeded.",
                    details={"error": str(e)},
                )
            if getattr(e, "code", None) in (408, 504) or "timeout" in str(e).lower() or "deadline" in str(e).lower():
                raise ProviderExecutionError(
                    f"Gemini request timed out after {self.timeout_seconds}s.",
                    details={"timeout": self.timeout_seconds, "error": str(e)},
                )
            raise ProviderExecutionError(
                f"Gemini API error: {getattr(e, 'message', None) or str(e)}",
                details={"code": getattr(e, "code", None), "error": str(e)},
            )
        except (httpx.TimeoutException, TimeoutError) as e:
            raise ProviderExecutionError(
                f"Gemini request timed out after {self.timeout_seconds}s.",
                details={"timeout": self.timeout_seconds, "error": str(e)},
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
        thought_signature: Optional[bytes] = None,
    ) -> ProviderStepResult:
        """Feeds tool execution output back to Gemini model as a FunctionResponse."""
        try:
            part = types.Part.from_function_response(
                name=tool_name,
                response={"result": result},
            )
            response = session.chat.send_message(part)
            return self._extract_step_result(response)
        except errors.APIError as e:
            if getattr(e, "code", None) == 429 or "quota" in str(e).lower() or "resource_exhausted" in str(e).lower():
                raise ProviderExecutionError(
                    "Gemini API quota exceeded during tool feedback.",
                    details={"tool_name": tool_name, "error": str(e)},
                )
            if getattr(e, "code", None) in (408, 504) or "timeout" in str(e).lower() or "deadline" in str(e).lower():
                raise ProviderExecutionError(
                    f"Gemini request timed out during tool result return ({self.timeout_seconds}s).",
                    details={"tool_name": tool_name, "error": str(e)},
                )
            raise ProviderExecutionError(
                f"Gemini API error during tool feedback: {str(e)}",
                details={"tool_name": tool_name, "error": str(e)},
            )
        except (httpx.TimeoutException, TimeoutError) as e:
            raise ProviderExecutionError(
                f"Gemini request timed out during tool result return ({self.timeout_seconds}s).",
                details={"tool_name": tool_name, "error": str(e)},
            )
        except Exception as e:
            if isinstance(e, (ProviderConfigurationError, ProviderExecutionError, MalformedModelResponseError)):
                raise
            raise ProviderExecutionError(
                f"Unexpected error sending tool result to Gemini: {str(e)}",
                details={"tool_name": tool_name, "error": str(e)},
            )
