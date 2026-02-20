"""
API routes for Session Handoffs.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..config.logfire_config import get_logger
from ..services.handoff_service import get_handoff_service

logger = get_logger(__name__)
router = APIRouter(prefix="/api/handoffs", tags=["Session Handoffs"])


# Request Models
class CreateHandoffRequest(BaseModel):
    session_id: str = Field(..., description="UUID of the session to hand off")
    from_agent: str = Field(..., description="Agent initiating the handoff")
    to_agent: str = Field(..., description="Agent that should receive the work")
    context: dict | None = Field(default_factory=dict, description="Structured context payload")
    notes: str | None = Field(None, description="Free-text instructions for the receiving agent")
    metadata: dict | None = Field(default_factory=dict, description="Additional metadata")


@router.post("", response_model=dict)
async def create_handoff(request: CreateHandoffRequest):
    """Create a new pending handoff between agents."""
    try:
        service = get_handoff_service()
        handoff = await service.create_handoff(
            session_id=request.session_id,
            from_agent=request.from_agent,
            to_agent=request.to_agent,
            context=request.context,
            notes=request.notes,
            metadata=request.metadata,
        )
        return {"success": True, "handoff": handoff}
    except Exception as e:
        logger.error(f"Error creating handoff: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=dict)
async def list_handoffs(
    session_id: str | None = Query(None, description="Filter by session UUID"),
    agent: str | None = Query(None, description="Filter by to_agent name"),
    status: str | None = Query(None, description="Filter by status"),
):
    """List handoffs with optional filters."""
    try:
        service = get_handoff_service()
        handoffs = await service.list_handoffs(
            session_id=session_id,
            agent=agent,
            status=status,
        )
        return {"success": True, "handoffs": handoffs, "count": len(handoffs)}
    except Exception as e:
        logger.error(f"Error listing handoffs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending/{agent}", response_model=dict)
async def get_pending_handoffs(agent: str):
    """Get all pending handoffs addressed to a specific agent."""
    try:
        service = get_handoff_service()
        handoffs = await service.get_pending_handoffs(agent)
        return {"success": True, "handoffs": handoffs, "count": len(handoffs)}
    except Exception as e:
        logger.error(f"Error getting pending handoffs for agent {agent}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{handoff_id}", response_model=dict)
async def get_handoff(handoff_id: str):
    """Get a specific handoff by ID."""
    try:
        service = get_handoff_service()
        handoff = await service.get_handoff(handoff_id)
        if not handoff:
            raise HTTPException(status_code=404, detail=f"Handoff '{handoff_id}' not found")
        return {"success": True, "handoff": handoff}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting handoff {handoff_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{handoff_id}/accept", response_model=dict)
async def accept_handoff(handoff_id: str):
    """Accept a pending handoff."""
    try:
        service = get_handoff_service()
        handoff = await service.accept_handoff(handoff_id)
        return {"success": True, "handoff": handoff}
    except Exception as e:
        logger.error(f"Error accepting handoff {handoff_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{handoff_id}/complete", response_model=dict)
async def complete_handoff(handoff_id: str):
    """Complete an accepted handoff."""
    try:
        service = get_handoff_service()
        handoff = await service.complete_handoff(handoff_id)
        return {"success": True, "handoff": handoff}
    except Exception as e:
        logger.error(f"Error completing handoff {handoff_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{handoff_id}/reject", response_model=dict)
async def reject_handoff(handoff_id: str):
    """Reject a pending handoff."""
    try:
        service = get_handoff_service()
        handoff = await service.reject_handoff(handoff_id)
        return {"success": True, "handoff": handoff}
    except Exception as e:
        logger.error(f"Error rejecting handoff {handoff_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
