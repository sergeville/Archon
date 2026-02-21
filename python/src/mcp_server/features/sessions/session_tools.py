"""
Session management tools for Archon MCP Server.

Provides access to agent work sessions, session events, and semantic search
capabilities for short-term memory tracking.
"""

import json
import logging
from typing import Any
from urllib.parse import urljoin

import httpx
from mcp.server.fastmcp import Context, FastMCP

from src.mcp_server.utils.error_handling import MCPErrorFormatter
from src.mcp_server.utils.timeout_config import get_default_timeout
from src.server.config.service_discovery import get_api_url

logger = logging.getLogger(__name__)

# Optimization constants
MAX_DESCRIPTION_LENGTH = 1000
DEFAULT_PAGE_SIZE = 10


def truncate_text(text: str, max_length: int = MAX_DESCRIPTION_LENGTH) -> str:
    """Truncate text to maximum length with ellipsis."""
    if text and len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text


def optimize_session_response(session: dict) -> dict:
    """Optimize session object for MCP response."""
    session = session.copy()  # Don't modify original

    # Truncate summary if present
    if "summary" in session and session["summary"]:
        session["summary"] = truncate_text(session["summary"])

    # Replace events array with count
    if "events" in session and isinstance(session["events"], list):
        session["events_count"] = len(session["events"])
        # Keep only first few events for context
        session["events"] = session["events"][:3]

    return session


def register_session_tools(mcp: FastMCP):
    """Register session management tools with the MCP server."""

    @mcp.tool()
    async def find_sessions(
        ctx: Context,
        session_id: str | None = None,  # Get specific session
        agent: str | None = None,  # Filter by agent
        project_id: str | None = None,  # Filter by project
        limit: int = DEFAULT_PAGE_SIZE,
    ) -> str:
        """
        Find and retrieve agent sessions.

        Args:
            session_id: Get specific session by ID (returns full details with events)
            agent: Filter sessions by agent name (claude, gemini, gpt, user)
            project_id: Filter sessions by project UUID
            limit: Maximum number of sessions to return (default: 10)

        Returns:
            JSON array of sessions or single session with events

        Examples:
            find_sessions() # All recent sessions
            find_sessions(agent="claude") # Claude's sessions
            find_sessions(session_id="uuid-here") # Get specific session
            find_sessions(project_id="uuid", limit=5) # Project sessions
        """
        try:
            api_url = get_api_url()
            timeout = get_default_timeout()

            # Single session get mode
            if session_id:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(
                        urljoin(api_url, f"/api/sessions/{session_id}")
                    )

                    if response.status_code == 200:
                        result = response.json()
                        return json.dumps({"success": True, "session": result["session"]})
                    elif response.status_code == 404:
                        return json.dumps({"success": False, "error": f"Session {session_id} not found"})
                    else:
                        return MCPErrorFormatter.format_http_error(response)

            # List sessions mode
            params = {}
            if agent:
                params["agent"] = agent
            if project_id:
                params["project_id"] = project_id
            if limit:
                params["limit"] = limit

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(
                    urljoin(api_url, "/api/sessions"),
                    params=params
                )

                if response.status_code == 200:
                    result = response.json()
                    sessions = result.get("sessions", [])

                    # Optimize list response
                    optimized_sessions = [
                        optimize_session_response(s) for s in sessions
                    ]

                    return json.dumps({
                        "success": True,
                        "sessions": optimized_sessions,
                        "total": len(optimized_sessions)
                    })
                else:
                    return MCPErrorFormatter.format_http_error(response)

        except httpx.TimeoutException:
            return MCPErrorFormatter.format_timeout_error("Session retrieval timed out")
        except Exception as e:
            return MCPErrorFormatter.format_generic_error(f"Failed to retrieve sessions: {str(e)}")

    @mcp.tool()
    async def manage_session(
        ctx: Context,
        action: str,  # "create" | "end" | "update"
        agent: str | None = None,  # Required for create
        session_id: str | None = None,  # Required for end/update
        project_id: str | None = None,  # Optional for create
        summary: str | None = None,  # Optional for end/update
        context: dict[str, Any] | None = None,  # Optional for create/update
        metadata: dict[str, Any] | None = None,  # Optional for create/end/update
    ) -> str:
        """
        Manage agent sessions (create, end, update).

        Actions:
        - "create": Start a new session for an agent
        - "end": End a session (optionally with summary)
        - "update": Update session context or metadata
        - "summarize": Generate an AI summary of a session using Claude

        Args:
            action: Operation to perform
            agent: Agent name (required for create)
            session_id: Session UUID (required for end/update/summarize)
            project_id: Optional project UUID (for create)
            summary: Session summary (for end/update)
            context: Session context data (for create/update)
            metadata: Additional metadata (for create/end/update)

        Returns:
            JSON with created/updated session

        Examples:
            manage_session(action="create", agent="claude", project_id="uuid")
            manage_session(action="end", session_id="uuid", summary="Completed Phase 2")
            manage_session(action="update", session_id="uuid", metadata={"status": "active"})
            manage_session(action="summarize", session_id="uuid")
        """
        try:
            api_url = get_api_url()
            timeout = get_default_timeout()

            if action == "create":
                if not agent:
                    return json.dumps({"success": False, "error": "agent is required for create action"})

                payload = {"agent": agent}
                if project_id:
                    payload["project_id"] = project_id
                if context:
                    payload["context"] = context
                if metadata:
                    payload["metadata"] = metadata

                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        urljoin(api_url, "/api/sessions"),
                        json=payload
                    )

                    if response.status_code == 200:
                        result = response.json()
                        return json.dumps({"success": True, "session": result["session"]})
                    else:
                        return MCPErrorFormatter.format_http_error(response)

            elif action == "end":
                if not session_id:
                    return json.dumps({"success": False, "error": "session_id is required for end action"})

                payload = {}
                if summary:
                    payload["summary"] = summary
                if metadata:
                    payload["metadata"] = metadata

                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        urljoin(api_url, f"/api/sessions/{session_id}/end"),
                        json=payload
                    )

                    if response.status_code == 200:
                        result = response.json()
                        return json.dumps({"success": True, "session": result["session"]})
                    elif response.status_code == 404:
                        return json.dumps({"success": False, "error": f"Session {session_id} not found"})
                    else:
                        return MCPErrorFormatter.format_http_error(response)

            elif action == "update":
                if not session_id:
                    return json.dumps({"success": False, "error": "session_id is required for update action"})

                payload = {}
                if summary:
                    payload["summary"] = summary
                if context:
                    payload["context"] = context
                if metadata:
                    payload["metadata"] = metadata

                if not payload:
                    return json.dumps({"success": False, "error": "At least one field (summary, context, metadata) is required for update"})

                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.put(
                        urljoin(api_url, f"/api/sessions/{session_id}"),
                        json=payload
                    )

                    if response.status_code == 200:
                        result = response.json()
                        return json.dumps({"success": True, "session": result["session"]})
                    elif response.status_code == 404:
                        return json.dumps({"success": False, "error": f"Session {session_id} not found"})
                    else:
                        return MCPErrorFormatter.format_http_error(response)

            elif action == "summarize":
                if not session_id:
                    return json.dumps({"success": False, "error": "session_id is required for summarize action"})

                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        urljoin(api_url, f"/api/sessions/{session_id}/summarize")
                    )

                    if response.status_code == 200:
                        result = response.json()
                        return json.dumps({"success": True, "session": result["session"]})
                    elif response.status_code == 404:
                        return json.dumps({"success": False, "error": f"Session {session_id} not found"})
                    else:
                        return MCPErrorFormatter.format_http_error(response)

            else:
                return json.dumps({
                    "success": False,
                    "error": f"Invalid action: {action}. Must be 'create', 'end', 'update', or 'summarize'"
                })

        except httpx.TimeoutException:
            return MCPErrorFormatter.format_timeout_error("Session management timed out")
        except Exception as e:
            return MCPErrorFormatter.format_generic_error(f"Failed to manage session: {str(e)}")

    @mcp.tool()
    async def log_session_event(
        ctx: Context,
        session_id: str,
        event_type: str,
        event_data: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Log an event within an agent session.

        Event types:
        - task_created: Agent created a task
        - task_updated: Agent updated a task
        - task_completed: Agent completed a task
        - decision_made: Agent made a decision
        - error_encountered: Error occurred
        - pattern_identified: Pattern recognized
        - context_shared: Context shared with another agent

        Args:
            session_id: Session UUID to log event to
            event_type: Type of event (see above)
            event_data: Event-specific data (JSON)
            metadata: Optional event metadata

        Returns:
            JSON with logged event

        Examples:
            log_session_event(
                session_id="uuid",
                event_type="task_created",
                event_data={"task_id": "123", "title": "New task"}
            )
            log_session_event(
                session_id="uuid",
                event_type="decision_made",
                event_data={"decision": "use pgvector", "reasoning": "..."}
            )
        """
        try:
            api_url = get_api_url()
            timeout = get_default_timeout()

            payload = {
                "session_id": session_id,
                "event_type": event_type,
                "event_data": event_data
            }
            if metadata:
                payload["metadata"] = metadata

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    urljoin(api_url, "/api/sessions/events"),
                    json=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    return json.dumps({"success": True, "event": result["event"]})
                else:
                    return MCPErrorFormatter.format_http_error(response)

        except httpx.TimeoutException:
            return MCPErrorFormatter.format_timeout_error("Event logging timed out")
        except Exception as e:
            return MCPErrorFormatter.format_generic_error(f"Failed to log event: {str(e)}")

    @mcp.tool()
    async def search_sessions_semantic(
        ctx: Context,
        query: str,
        limit: int = 10,
        threshold: float = 0.7,
    ) -> str:
        """
        Search sessions using semantic similarity.

        Uses vector embeddings to find sessions with similar content to the query.
        Particularly useful for finding sessions about specific topics, decisions,
        or patterns without exact keyword matching.

        Args:
            query: Search query text
            limit: Maximum number of results (default: 10)
            threshold: Minimum similarity score 0-1 (default: 0.7, higher = more similar)

        Returns:
            JSON array of matching sessions with similarity scores

        Examples:
            search_sessions_semantic(query="database migration errors")
            search_sessions_semantic(query="authentication implementation", limit=5)
            search_sessions_semantic(query="vector embeddings", threshold=0.8)
        """
        try:
            api_url = get_api_url()
            timeout = get_default_timeout()

            payload = {
                "query": query,
                "limit": limit,
                "threshold": threshold
            }

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    urljoin(api_url, "/api/sessions/search"),
                    json=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    sessions = result.get("sessions", [])

                    return json.dumps({
                        "success": True,
                        "sessions": sessions,
                        "total": len(sessions),
                        "query": query,
                        "threshold": threshold
                    })
                else:
                    return MCPErrorFormatter.format_http_error(response)

        except httpx.TimeoutException:
            return MCPErrorFormatter.format_timeout_error("Session search timed out")
        except Exception as e:
            return MCPErrorFormatter.format_generic_error(f"Failed to search sessions: {str(e)}")

    @mcp.tool()
    async def get_agent_context(
        ctx: Context,
        agent: str,
        mode: str = "last",  # "last" | "recent"
        days: int = 7,  # For recent mode
        limit: int = 10,  # For recent mode
    ) -> str:
        """
        Get contextual information about an agent's recent work.

        Modes:
        - "last": Get the most recent session (useful for resuming work)
        - "recent": Get recent sessions from last N days

        Args:
            agent: Agent name (claude, gemini, gpt, user)
            mode: Context mode ("last" or "recent")
            days: Number of days to look back (for recent mode, default: 7)
            limit: Maximum sessions to return (for recent mode, default: 10)

        Returns:
            JSON with agent's session(s) and events

        Examples:
            get_agent_context(agent="claude", mode="last")
            get_agent_context(agent="claude", mode="recent", days=7, limit=10)
        """
        try:
            api_url = get_api_url()
            timeout = get_default_timeout()

            if mode == "last":
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(
                        urljoin(api_url, f"/api/sessions/agents/{agent}/last")
                    )

                    if response.status_code == 200:
                        result = response.json()
                        return json.dumps({"success": True, "session": result["session"]})
                    elif response.status_code == 404:
                        return json.dumps({
                            "success": True,
                            "session": None,
                            "message": f"No previous sessions found for {agent}"
                        })
                    else:
                        return MCPErrorFormatter.format_http_error(response)

            elif mode == "recent":
                params = {"days": days, "limit": limit}

                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(
                        urljoin(api_url, f"/api/sessions/agents/{agent}/recent"),
                        params=params
                    )

                    if response.status_code == 200:
                        result = response.json()
                        sessions = result.get("sessions", [])

                        # Optimize session responses
                        optimized_sessions = [
                            optimize_session_response(s) for s in sessions
                        ]

                        return json.dumps({
                            "success": True,
                            "sessions": optimized_sessions,
                            "total": len(optimized_sessions),
                            "period_days": days
                        })
                    else:
                        return MCPErrorFormatter.format_http_error(response)

            else:
                return json.dumps({
                    "success": False,
                    "error": f"Invalid mode: {mode}. Must be 'last' or 'recent'"
                })

        except httpx.TimeoutException:
            return MCPErrorFormatter.format_timeout_error("Context retrieval timed out")
        except Exception as e:
            return MCPErrorFormatter.format_generic_error(f"Failed to get agent context: {str(e)}")
