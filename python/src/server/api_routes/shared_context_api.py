"""
API routes for Shared Context Board.
"""
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..config.logfire_config import get_logger
from ..services.shared_context_service import get_shared_context_service

logger = get_logger(__name__)
router = APIRouter(prefix="/api/context", tags=["Shared Context"])


# Request Models
class SetContextRequest(BaseModel):
    value: Any = Field(..., description="JSON-serialisable value to store")
    set_by: str = Field(..., description="Agent or user writing this value")
    session_id: str | None = Field(None, description="Optional linked session UUID")
    expires_at: str | None = Field(None, description="Optional ISO-8601 expiry timestamp")


@router.put("/{key}", response_model=dict)
async def set_context(key: str, request: SetContextRequest):
    """Set or update a context entry by key."""
    try:
        service = get_shared_context_service()
        entry = await service.set_context(
            key=key,
            value=request.value,
            set_by=request.set_by,
            session_id=request.session_id,
            expires_at=request.expires_at,
        )
        return {"success": True, "context": entry}
    except Exception as e:
        logger.error(f"Error setting context key '{key}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=dict)
async def list_context(
    prefix: str | None = Query(None, description="Filter keys by prefix"),
):
    """List all context entries with optional prefix filter."""
    try:
        service = get_shared_context_service()
        entries = await service.list_context(prefix=prefix)
        return {"success": True, "context": entries, "count": len(entries)}
    except Exception as e:
        logger.error(f"Error listing context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{key}/history", response_model=dict)
async def get_context_history(
    key: str,
    limit: int = Query(20, ge=1, le=100, description="Max history records"),
):
    """Get the change history for a context key."""
    try:
        service = get_shared_context_service()
        history = await service.get_history(key, limit=limit)
        return {"success": True, "history": history, "count": len(history)}
    except Exception as e:
        logger.error(f"Error getting history for context key '{key}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{key}", response_model=dict)
async def get_context(key: str):
    """Get a context entry by key."""
    try:
        service = get_shared_context_service()
        entry = await service.get_context(key)
        if not entry:
            raise HTTPException(status_code=404, detail=f"Context key '{key}' not found")
        return {"success": True, "context": entry}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting context key '{key}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{key}", response_model=dict)
async def delete_context(key: str):
    """Delete a context entry by key."""
    try:
        service = get_shared_context_service()
        deleted = await service.delete_context(key)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Context key '{key}' not found")
        return {"success": True, "deleted": key}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting context key '{key}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
