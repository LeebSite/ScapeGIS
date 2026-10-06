"""
Base Spatial AI Provider Abstraction

Defines the contract for LLM providers (e.g. Gemini, Anthropic, OpenAI).
Isolates ScapeGIS core spatial tools, services, and authorization
from any specific third-party AI SDK.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ToolCallRequest(BaseModel):
    """Normalized representation of an LLM tool/function call request."""
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    call_id: Optional[str] = None


class ProviderStepResult(BaseModel):
    """
    Result of a single conversational turn from an AI provider.
    Either contains requested tool calls or the final natural language text.
    """
    text: Optional[str] = None
    tool_calls: List[ToolCallRequest] = Field(default_factory=list)
    is_tool_call: bool = False
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseSpatialAIProvider(ABC):
    """
    Abstract interface for AI reasoning providers.
    Supports starting a session with tools, sending user messages,
    and feeding back tool execution outputs for iterative synthesis.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_seconds: int = 30,
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    def start_conversation(
        self,
        system_instruction: str,
        tool_declarations: List[Dict[str, Any]],
    ) -> Any:
        """
        Initializes a stateful conversation session configured with
        system instructions and tool definitions.
        """
        pass

    @abstractmethod
    def send_user_message(
        self,
        session: Any,
        message: str,
    ) -> ProviderStepResult:
        """
        Submits a user message to the active session and returns
        the provider's response (tool call requests or text).
        """
        pass

    @abstractmethod
    def send_tool_result(
        self,
        session: Any,
        tool_name: str,
        result: Dict[str, Any],
    ) -> ProviderStepResult:
        """
        Feeds back the execution result of a tool to the model,
        receiving either subsequent tool calls or final text synthesis.
        """
        pass
