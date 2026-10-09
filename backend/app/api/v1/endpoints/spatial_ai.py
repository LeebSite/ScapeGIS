"""
Spatial AI Analysis Endpoints

Provides backend integration endpoint for Google Gemini spatial reasoning
and multi-turn tool calling orchestration.
Strictly enforces JWT authentication and tenant workspace authorization.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.db.models.user import User
from app.spatial_ai.agent import GeminiSpatialAgent
from app.spatial_ai.schemas import SpatialAIAnalysisRequest, SpatialAIChatRequest, SpatialAIResponse
from app.spatial_ai.exceptions import (
    SpatialAIAuthorizationError,
    ProviderConfigurationError,
    ProviderExecutionError,
    ToolLoopExceededError,
    SpatialAIError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/spatial-ai", tags=["Spatial AI"])


@router.post(
    "/analyze",
    response_model=SpatialAIResponse,
    summary="Execute Gemini spatial analysis with controlled tool contract",
    description=(
        "Analyzes a natural language developer query regarding a specific coordinate location. "
        "Orchestrates Google Gemini through verified PostGIS tools, strictly scoped "
        "to the authorized workspace and active GIS datasets."
    ),
)
def analyze_spatial_query(
    request: SpatialAIAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SpatialAIResponse:
    """
    Executes the spatial AI reasoning pipeline:
    1. Authenticated User & Workspace Authorization Check
    2. PostGIS Ground-Truth Tool Dispatch
    3. Gemini Analytical Synthesis
    4. Provenance & MapAction derivation
    """
    try:
        agent = GeminiSpatialAgent()
        return agent.analyze(
            db=db,
            user=current_user,
            request=request,
        )
    except SpatialAIAuthorizationError as e:
        logger.warning("Spatial AI authorization failed: %s", e.message)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message,
        )
    except ProviderConfigurationError as e:
        logger.error("Spatial AI configuration error: %s", e.message, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Spatial AI service configuration is invalid or missing required credentials.",
        )
    except ProviderExecutionError as e:
        logger.error("Spatial AI provider execution error: %s", e.message, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Spatial AI provider service encountered an error while processing the request.",
        )
    except ToolLoopExceededError as e:
        logger.warning("Spatial AI tool loop limit exceeded: %s", e.message)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Spatial AI reasoning exceeded maximum allowed tool executions.",
        )
    except SpatialAIError as e:
        logger.warning("Spatial AI processing error: %s", e.message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request or error encountered during spatial AI processing.",
        )
    except Exception as e:
        logger.exception("Unexpected error during spatial AI processing: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal error occurred during spatial AI processing.",
        )


@router.post(
    "/chat",
    response_model=SpatialAIResponse,
    summary="Execute multi-turn Spatial AI chat with controlled tool contract",
    description=(
        "Processes a natural language chat message with bounded conversation history. "
        "Orchestrates spatial reasoning through verified PostGIS tools, strictly scoped "
        "to the authorized workspace and active GIS datasets."
    ),
)
def chat_spatial_query(
    request: SpatialAIChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SpatialAIResponse:
    """
    Executes the multi-turn Spatial AI chat reasoning pipeline:
    1. Authenticated User & Workspace Authorization Check
    2. Bounded and Sanitized History Injection
    3. PostGIS Ground-Truth Tool Dispatch
    4. Provider Analytical Synthesis
    5. Provenance & MapAction derivation
    """
    try:
        agent = GeminiSpatialAgent()
        return agent.chat(
            db=db,
            user=current_user,
            request=request,
        )
    except SpatialAIAuthorizationError as e:
        logger.warning("Spatial AI authorization failed: %s", e.message)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message,
        )
    except ProviderConfigurationError as e:
        logger.error("Spatial AI configuration error: %s", e.message, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Spatial AI service configuration is invalid or missing required credentials.",
        )
    except ProviderExecutionError as e:
        logger.error("Spatial AI provider execution error: %s", e.message, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Spatial AI provider service encountered an error while processing the request.",
        )
    except ToolLoopExceededError as e:
        logger.warning("Spatial AI tool loop limit exceeded: %s", e.message)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Spatial AI reasoning exceeded maximum allowed tool executions.",
        )
    except SpatialAIError as e:
        logger.warning("Spatial AI processing error: %s", e.message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request or error encountered during spatial AI processing.",
        )
    except Exception as e:
        logger.exception("Unexpected error during spatial AI chat processing: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal error occurred during spatial AI processing.",
        )
