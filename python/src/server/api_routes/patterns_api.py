"""
API routes for Pattern Learning System.
"""
from typing import Any, Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..config.logfire_config import get_logger
from ..services.pattern_service import get_pattern_service

logger = get_logger(__name__)
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
        logger.error(f"Error creating pattern: {e}", exc_info=True)
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
        logger.error(f"Error recording observation: {e}", exc_info=True)
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
        logger.error(f"Error searching patterns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=dict)
async def list_patterns(
    pattern_type: Optional[str] = Query(None, description="Filter by type"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
):
    """List patterns with optional filters."""
    try:
        service = get_pattern_service()
        patterns = await service.list_patterns(
            pattern_type=pattern_type,
            domain=domain,
            limit=limit
        )
        return {"success": True, "patterns": patterns, "count": len(patterns)}
    except Exception as e:
        logger.error(f"Error listing patterns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=dict)
async def get_pattern_stats():
    """Get global pattern statistics."""
    try:
        service = get_pattern_service()
        stats = await service.get_pattern_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        logger.error(f"Error getting pattern stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract/{session_id}", response_model=dict)
async def extract_patterns_from_session(session_id: UUID):
    """Analyze a session and extract reusable patterns from it."""
    try:
        service = get_pattern_service()
        patterns = await service.extract_patterns_from_session(session_id)
        return {"success": True, "patterns": patterns, "count": len(patterns)}
    except Exception as e:
        logger.error(f"Error extracting patterns from session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{pattern_id}", response_model=dict)
async def get_pattern(pattern_id: UUID):
    """Get pattern details with observation stats."""
    try:
        service = get_pattern_service()
        pattern = await service.get_pattern(pattern_id)
        if not pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")
        return {"success": True, "pattern": pattern}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pattern {pattern_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
