"""
Sessions API endpoints for Archon

Handles:
- Session management (CRUD operations)
- Event logging within sessions
- Semantic search across sessions
- Agent activity tracking
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi import status as http_status
from pydantic import BaseModel

from ..config.logfire_config import get_logger
from ..services.session_service import SessionService

logger = get_logger(__name__)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


# Request/Response Models
class CreateSessionRequest(BaseModel):
    agent: str
    project_id: str | None = None
    context: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class UpdateSessionRequest(BaseModel):
    summary: str | None = None
    context: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class EndSessionRequest(BaseModel):
    summary: str | None = None
    metadata: dict[str, Any] | None = None


class LogEventRequest(BaseModel):
    session_id: str
    event_type: str
    event_data: dict[str, Any]
    metadata: dict[str, Any] | None = None


class SearchSessionsRequest(BaseModel):
    query: str
    limit: int = 10
    threshold: float = 0.7


# Initialize service
session_service = SessionService()


# Endpoints

@router.post("")
async def create_session(request: CreateSessionRequest):
    """Create a new session for an agent"""
    try:
        session = await session_service.create_session(
            agent=request.agent,
            project_id=request.project_id,
            context=request.context or {},
            metadata=request.metadata or {}
        )
        return {
            "message": "Session created successfully",
            "session": session
        }
    except Exception as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("")
async def list_sessions(
    agent: str | None = None,
    project_id: str | None = None,
    limit: int = 50
):
    """List sessions with optional filtering"""
    try:
        sessions = await session_service.list_sessions(
            agent=agent,
            project_id=project_id,
            limit=limit
        )
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Error listing sessions: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}"
        )


@router.get("/{session_id}")
async def get_session(session_id: str):
    """Get a specific session by ID"""
    try:
        session = await session_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        return {"session": session}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session: {str(e)}"
        )


@router.put("/{session_id}")
async def update_session(session_id: str, request: UpdateSessionRequest):
    """Update session details"""
    try:
        # Build updates dict
        updates = {}
        if request.summary is not None:
            updates["summary"] = request.summary
        if request.context is not None:
            updates["context"] = request.context
        if request.metadata is not None:
            updates["metadata"] = request.metadata

        session = await session_service.update_session(session_id, updates)
        if not session:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )

        return {
            "message": "Session updated successfully",
            "session": session
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session: {str(e)}"
        )


@router.post("/{session_id}/end")
async def end_session(session_id: str, request: EndSessionRequest):
    """End a session and optionally generate summary"""
    try:
        session = await session_service.end_session(
            session_id=session_id,
            summary=request.summary,
            metadata=request.metadata
        )
        if not session:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )

        return {
            "message": "Session ended successfully",
            "session": session
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending session: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end session: {str(e)}"
        )


@router.post("/events")
async def log_event(request: LogEventRequest):
    """Log an event within a session"""
    try:
        event = await session_service.add_event(
            session_id=request.session_id,
            event_type=request.event_type,
            event_data=request.event_data,
            metadata=request.metadata or {}
        )
        return {
            "message": "Event logged successfully",
            "event": event
        }
    except Exception as e:
        logger.error(f"Error logging event: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log event: {str(e)}"
        )


@router.get("/{session_id}/events")
async def get_session_events(session_id: str, limit: int = 100):
    """Get all events for a session"""
    try:
        events = await session_service.get_session_events(
            session_id=session_id,
            limit=limit
        )
        return {"events": events}
    except Exception as e:
        logger.error(f"Error getting session events: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session events: {str(e)}"
        )


@router.post("/search")
async def search_sessions(request: SearchSessionsRequest):
    """Search sessions using semantic similarity"""
    try:
        sessions = await session_service.search_sessions(
            query=request.query,
            limit=request.limit,
            threshold=request.threshold
        )
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Error searching sessions: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search sessions: {str(e)}"
        )


@router.get("/agents/{agent}/last")
async def get_last_session(agent: str):
    """Get the most recent session for an agent"""
    try:
        session = await session_service.get_last_session(agent)
        if not session:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"No sessions found for agent {agent}"
            )
        return {"session": session}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting last session: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get last session: {str(e)}"
        )


@router.get("/agents/{agent}/recent")
async def get_recent_sessions(agent: str, days: int = 7, limit: int = 20):
    """Get recent sessions for an agent"""
    try:
        sessions = await session_service.get_recent_sessions(
            agent=agent,
            days=days,
            limit=limit
        )
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Error getting recent sessions: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent sessions: {str(e)}"
        )


@router.post("/search/all")
async def search_all_memory(request: SearchSessionsRequest):
    """
    Unified semantic search across all memory layers (sessions, tasks, projects).

    Returns results from sessions, tasks, and projects, ranked by similarity.
    Each result includes a 'type' field indicating which layer it came from.
    """
    try:
        results = await session_service.search_all_memory(
            query=request.query,
            limit=request.limit,
            threshold=request.threshold
        )
        return {
            "query": request.query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Error in unified memory search: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search memory: {str(e)}"
        )
