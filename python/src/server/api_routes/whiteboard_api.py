"""
Whiteboard API endpoints for Archon

Provides access to the real-time whiteboard showing:
- Active agent sessions
- Tasks currently in progress
- Recent activity events
"""

from fastapi import APIRouter, HTTPException
from fastapi import status as http_status

from ..config.logfire_config import get_logger
from ..services.whiteboard_service import WhiteboardService

logger = get_logger(__name__)

router = APIRouter(prefix="/api/whiteboard", tags=["whiteboard"])

# Initialize service
whiteboard_service = WhiteboardService()


@router.get("")
async def get_whiteboard():
    """
    Get the current whiteboard state.

    Returns the whiteboard document containing:
    - active_sessions: List of currently active agent sessions
    - active_tasks: List of tasks with status 'doing'
    - recent_events: Recent task/session lifecycle events (last 50)
    """
    try:
        success, result = await whiteboard_service.get_whiteboard()

        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=result.get("error", "Whiteboard not found")
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting whiteboard: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get whiteboard: {str(e)}"
        )


@router.get("/active-sessions")
async def get_active_sessions():
    """Get only the active sessions from the whiteboard"""
    try:
        success, result = await whiteboard_service.get_whiteboard()

        if not success:
            return {"active_sessions": []}

        whiteboard = result.get("whiteboard", {})
        content = whiteboard.get("content", {})

        return {
            "active_sessions": content.get("active_sessions", []),
            "count": len(content.get("active_sessions", []))
        }

    except Exception as e:
        logger.error(f"Error getting active sessions: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active sessions: {str(e)}"
        )


@router.get("/active-tasks")
async def get_active_tasks():
    """Get only the active tasks (status='doing') from the whiteboard"""
    try:
        success, result = await whiteboard_service.get_whiteboard()

        if not success:
            return {"active_tasks": []}

        whiteboard = result.get("whiteboard", {})
        content = whiteboard.get("content", {})

        return {
            "active_tasks": content.get("active_tasks", []),
            "count": len(content.get("active_tasks", []))
        }

    except Exception as e:
        logger.error(f"Error getting active tasks: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active tasks: {str(e)}"
        )


@router.get("/all-tasks")
async def get_all_tasks(project_id: str | None = None):
    """
    Get all tasks grouped by status for todo-list display.

    Args:
        project_id: Optional project ID filter
    """
    try:
        from ..services.projects.task_service import TaskService

        task_service = TaskService()
        success, result = task_service.list_tasks(
            project_id=project_id,
            include_closed=True  # Include done tasks
        )

        if not success:
            return {"tasks": [], "count": 0}

        tasks = result.get("tasks", [])

        # Group by status for todo-list display
        grouped = {
            "doing": [],
            "todo": [],
            "review": [],
            "done": []
        }

        for task in tasks:
            status = task.get("status", "todo")
            if status in grouped:
                grouped[status].append({
                    "task_id": task["id"],
                    "title": task["title"],
                    "status": status,
                    "assignee": task.get("assignee"),
                    "project_id": task.get("project_id"),
                    "updated_at": task.get("updated_at")
                })

        # Order: doing first (in progress), then todo, review, done
        ordered_tasks = (
            grouped["doing"] +
            grouped["todo"] +
            grouped["review"] +
            grouped["done"]
        )

        return {
            "tasks": ordered_tasks,
            "count": len(ordered_tasks),
            "grouped": grouped
        }

    except Exception as e:
        logger.error(f"Error getting all tasks: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get all tasks: {str(e)}"
        )


@router.get("/recent-events")
async def get_recent_events(limit: int = 20):
    """
    Get recent events from the whiteboard.

    Args:
        limit: Maximum number of events to return (default 20, max 50)
    """
    try:
        limit = min(limit, 50)  # Cap at 50

        success, result = await whiteboard_service.get_whiteboard()

        if not success:
            return {"recent_events": [], "count": 0}

        whiteboard = result.get("whiteboard", {})
        content = whiteboard.get("content", {})
        recent_events = content.get("recent_events", [])

        return {
            "recent_events": recent_events[:limit],
            "count": len(recent_events[:limit]),
            "total": len(recent_events)
        }

    except Exception as e:
        logger.error(f"Error getting recent events: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent events: {str(e)}"
        )


@router.post("/refresh")
async def refresh_whiteboard():
    """
    Manually refresh the whiteboard state.

    This endpoint can be used for:
    - Debugging
    - Forcing a sync after events may have been missed
    - Testing the whiteboard update mechanism
    """
    try:
        # Get current whiteboard
        success, result = await whiteboard_service.get_whiteboard()

        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Whiteboard not found"
            )

        whiteboard = result.get("whiteboard", {})
        content = whiteboard.get("content", {})

        # For now, just return current state
        # In future, could query DB for actual active sessions/tasks
        return {
            "message": "Whiteboard refreshed",
            "active_sessions_count": len(content.get("active_sessions", [])),
            "active_tasks_count": len(content.get("active_tasks", [])),
            "recent_events_count": len(content.get("recent_events", []))
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing whiteboard: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh whiteboard: {str(e)}"
        )
