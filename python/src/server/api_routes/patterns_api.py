"""
API routes for Pattern Learning System.
"""
from typing import Any, Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..services.pattern_service import get_pattern_service

router = APIRouter(prefix="/api/patterns", tags=["patterns"])


# Request Models
class PatternCreateRequest(BaseModel):
    pattern_type: str = Field(..., description="Type: success, failure, technical, process")
    domain: str = Field(..., description="Application domain")
    description: str = Field(..., description="Pattern description")
    action: str = Field(..., description="Core action")
    outcome: Optional[str] = None
    context: Optional[dict] = None
    metadata: Optional[dict] = None
    created_by: str = "user"


class ObservationCreateRequest(BaseModel):
    pattern_id: UUID
    session_id: Optional[UUID] = None
    success_rating: Optional[int] = Field(None, ge=1, le=5)
    feedback: Optional[str] = None
    metadata: Optional[dict] = None


class PatternSearchRequest(BaseModel):
    query: str
    limit: int = 10
    threshold: float = 0.7
    domain: Optional[str] = None


@router.post("", response_model=dict)
async def create_pattern(request: PatternCreateRequest):
    """Harvest a new pattern."""
    try:
        service = get_pattern_service()
        pattern = await service.harvest_pattern(
            pattern_type=request.pattern_type,
            domain=request.domain,
            description=request.description,
            action=request.action,
            outcome=request.outcome,
            context=request.context,
            metadata=request.metadata,
            created_by=request.created_by
        )
        return {"success": True, "pattern": pattern}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/observations", response_model=dict)
async def record_observation(request: ObservationCreateRequest):
    """Record an observation of a pattern."""
    try:
        service = get_pattern_service()
        observation = await service.record_observation(
            pattern_id=request.pattern_id,
            session_id=request.session_id,
            success_rating=request.success_rating,
            feedback=request.feedback,
            metadata=request.metadata
        )
        return {"success": True, "observation": observation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=dict)
async def search_patterns(request: PatternSearchRequest):
    """Search patterns semantically."""
    try:
        service = get_pattern_service()
        patterns = await service.search_patterns(
            query=request.query,
            limit=request.limit,
            threshold=request.threshold,
            domain=request.domain
        )
        return {"success": True, "patterns": patterns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{pattern_id}", response_model=dict)
async def get_pattern(pattern_id: UUID):
    """Get pattern details."""
    try:
        service = get_pattern_service()
        pattern = await service.get_pattern(pattern_id)
        if not pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")
        return {"success": True, "pattern": pattern}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
