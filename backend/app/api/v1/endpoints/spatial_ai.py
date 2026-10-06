"""
Spatial AI Analysis Endpoints

Provides backend integration endpoint for Google Gemini spatial reasoning
and multi-turn tool calling orchestration.
Strictly enforces JWT authentication and tenant workspace authorization.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.db.models.user import User
from app.spatial_ai.agent import GeminiSpatialAgent
from app.spatial_ai.schemas import SpatialAIAnalysisRequest, SpatialAIResponse
from app.spatial_ai.exceptions import (
    SpatialAIAuthorizationError,
    ProviderConfigurationError,
    ProviderExecutionError,
    ToolLoopExceededError,
    SpatialAIError,
)

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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message,
        )
    except ProviderConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Spatial AI configuration error: {e.message}",
        )
    except ProviderExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Spatial AI provider error: {e.message}",
        )
    except ToolLoopExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message,
        )
    except SpatialAIError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal error occurred during spatial AI processing.",
        )
