"""
Whiteboard Service for Archon

Manages the whiteboard document that displays real-time agent activity.
The whiteboard shows:
- Active sessions (what agents are currently working on)
- Active tasks (tasks currently in progress)
- Recent events (task/session lifecycle changes)
"""

from datetime import datetime, timezone
from typing import Any

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)


class WhiteboardService:
    """Service for managing the whiteboard document"""

    # Known whiteboard location from earlier conversation
    DEFAULT_PROJECT_ID = "6cc3ca3f-ad32-4cbf-98b3-975abbbddeee"
    DEFAULT_WHITEBOARD_ID = "8aeb549b-4cd1-4ff8-adda-87b0afbca9da"

    def __init__(self, supabase_client=None):
        """Initialize whiteboard service"""
        self.supabase_client = supabase_client or get_supabase_client()

    async def get_whiteboard(
        self, project_id: str = None, whiteboard_id: str = None
    ) -> tuple[bool, dict[str, Any]]:
        """
        Get the whiteboard document.

        Args:
            project_id: Project containing whiteboard (defaults to Archon project)
            whiteboard_id: Whiteboard document ID (defaults to main whiteboard)

        Returns:
            Tuple of (success, whiteboard_data)
        """
        try:
            project_id = project_id or self.DEFAULT_PROJECT_ID
            whiteboard_id = whiteboard_id or self.DEFAULT_WHITEBOARD_ID

            # Get project docs
            response = (
                self.supabase_client.table("archon_projects")
                .select("docs")
                .eq("id", project_id)
                .execute()
            )

            if not response.data:
                logger.warning(f"Project {project_id} not found")
                return False, {"error": f"Project {project_id} not found"}

            docs = response.data[0].get("docs", [])

            # Find whiteboard document
            whiteboard = None
            for doc in docs:
                if doc.get("id") == whiteboard_id:
                    whiteboard = doc
                    break

            if not whiteboard:
                logger.warning(f"Whiteboard {whiteboard_id} not found in project {project_id}")
                # Return empty whiteboard structure
                return True, {
                    "whiteboard": {
                        "id": whiteboard_id,
                        "project_id": project_id,
                        "content": {
                            "active_sessions": [],
                            "active_tasks": [],
                            "recent_events": []
                        }
                    }
                }

            return True, {
                "whiteboard": {
                    "id": whiteboard.get("id"),
                    "project_id": project_id,
                    "title": whiteboard.get("title"),
                    "content": whiteboard.get("content", {
                        "active_sessions": [],
                        "active_tasks": [],
                        "recent_events": []
                    }),
                    "updated_at": whiteboard.get("updated_at")
                }
            }

        except Exception as e:
            logger.error(f"Error getting whiteboard: {e}", exc_info=True)
            return False, {"error": f"Failed to get whiteboard: {str(e)}"}

    async def update_whiteboard(
        self,
        content: dict[str, Any],
        project_id: str = None,
        whiteboard_id: str = None
    ) -> tuple[bool, dict[str, Any]]:
        """
        Update the whiteboard content.

        Args:
            content: New whiteboard content (active_sessions, active_tasks, recent_events)
            project_id: Project containing whiteboard
            whiteboard_id: Whiteboard document ID

        Returns:
            Tuple of (success, result)
        """
        try:
            project_id = project_id or self.DEFAULT_PROJECT_ID
            whiteboard_id = whiteboard_id or self.DEFAULT_WHITEBOARD_ID

            # Get current project docs
            response = (
                self.supabase_client.table("archon_projects")
                .select("docs")
                .eq("id", project_id)
                .execute()
            )

            if not response.data:
                return False, {"error": f"Project {project_id} not found"}

            docs = response.data[0].get("docs", []).copy()

            # Find and update whiteboard
            found = False
            for i, doc in enumerate(docs):
                if doc.get("id") == whiteboard_id:
                    docs[i]["content"] = content
                    docs[i]["updated_at"] = datetime.now(timezone.utc).isoformat()
                    found = True
                    break

            if not found:
                # Create new whiteboard document
                new_whiteboard = {
                    "id": whiteboard_id,
                    "document_type": "whiteboard",
                    "title": "Whiteboard",
                    "content": content,
                    "status": "active",
                    "version": "1.0",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                docs.append(new_whiteboard)
                logger.info(f"Created new whiteboard document {whiteboard_id}")

            # Update project
            update_response = (
                self.supabase_client.table("archon_projects")
                .update({
                    "docs": docs,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                })
                .eq("id", project_id)
                .execute()
            )

            if update_response.data:
                logger.debug(f"Updated whiteboard {whiteboard_id}")
                return True, {"message": "Whiteboard updated successfully"}
            else:
                return False, {"error": "Failed to update whiteboard"}

        except Exception as e:
            logger.error(f"Error updating whiteboard: {e}", exc_info=True)
            return False, {"error": f"Failed to update whiteboard: {str(e)}"}

    async def add_session(
        self, session_id: str, agent: str, project_id: str = None, started_at: str = None
    ) -> tuple[bool, dict[str, Any]]:
        """
        Add an active session to the whiteboard.

        Args:
            session_id: Session UUID
            agent: Agent name (claude, gemini, etc.)
            project_id: Optional project the session is working on
            started_at: ISO timestamp when session started

        Returns:
            Tuple of (success, result)
        """
        try:
            success, result = await self.get_whiteboard()
            if not success:
                return False, result

            whiteboard = result["whiteboard"]
            content = whiteboard.get("content", {})
            active_sessions = content.get("active_sessions", [])

            # Check if session already exists
            session_exists = any(s.get("session_id") == session_id for s in active_sessions)
            if session_exists:
                logger.debug(f"Session {session_id} already on whiteboard")
                return True, {"message": "Session already active"}

            # Add new session
            new_session = {
                "session_id": session_id,
                "agent": agent,
                "project_id": project_id,
                "started_at": started_at or datetime.now(timezone.utc).isoformat(),
                "current_activity": "Session started"
            }
            active_sessions.append(new_session)

            content["active_sessions"] = active_sessions
            return await self.update_whiteboard(content)

        except Exception as e:
            logger.error(f"Error adding session to whiteboard: {e}", exc_info=True)
            return False, {"error": str(e)}

    async def remove_session(self, session_id: str) -> tuple[bool, dict[str, Any]]:
        """Remove a session from the whiteboard (when session ends)"""
        try:
            success, result = await self.get_whiteboard()
            if not success:
                return False, result

            whiteboard = result["whiteboard"]
            content = whiteboard.get("content", {})
            active_sessions = content.get("active_sessions", [])

            # Filter out the ended session
            content["active_sessions"] = [
                s for s in active_sessions if s.get("session_id") != session_id
            ]

            return await self.update_whiteboard(content)

        except Exception as e:
            logger.error(f"Error removing session from whiteboard: {e}", exc_info=True)
            return False, {"error": str(e)}

    async def update_task_status(
        self, task_id: str, title: str, status: str, assignee: str, project_id: str = None
    ) -> tuple[bool, dict[str, Any]]:
        """
        Update task on whiteboard (add to active if status is 'doing', remove otherwise).

        Args:
            task_id: Task UUID
            title: Task title
            status: Task status (todo, doing, review, done)
            assignee: Who is assigned to the task
            project_id: Optional project ID

        Returns:
            Tuple of (success, result)
        """
        try:
            success, result = await self.get_whiteboard()
            if not success:
                return False, result

            whiteboard = result["whiteboard"]
            content = whiteboard.get("content", {})
            active_tasks = content.get("active_tasks", [])

            # Remove task if it exists (we'll re-add if status is 'doing')
            active_tasks = [t for t in active_tasks if t.get("task_id") != task_id]

            # Add task if status is 'doing'
            if status == "doing":
                new_task = {
                    "task_id": task_id,
                    "title": title,
                    "status": status,
                    "assignee": assignee,
                    "project_id": project_id,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                active_tasks.append(new_task)

            content["active_tasks"] = active_tasks
            return await self.update_whiteboard(content)

        except Exception as e:
            logger.error(f"Error updating task on whiteboard: {e}", exc_info=True)
            return False, {"error": str(e)}

    async def add_event(
        self, event_type: str, event_data: dict[str, Any], max_events: int = 50
    ) -> tuple[bool, dict[str, Any]]:
        """
        Add an event to the recent events list on the whiteboard.

        Args:
            event_type: Type of event (task.created, session.started, etc.)
            event_data: Event payload
            max_events: Maximum number of recent events to keep (default 50)

        Returns:
            Tuple of (success, result)
        """
        try:
            success, result = await self.get_whiteboard()
            if not success:
                return False, result

            whiteboard = result["whiteboard"]
            content = whiteboard.get("content", {})
            recent_events = content.get("recent_events", [])

            # Add new event
            new_event = {
                "event_type": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": event_data
            }
            recent_events.insert(0, new_event)  # Add to front

            # Keep only most recent events
            content["recent_events"] = recent_events[:max_events]

            return await self.update_whiteboard(content)

        except Exception as e:
            logger.error(f"Error adding event to whiteboard: {e}", exc_info=True)
            return False, {"error": str(e)}
