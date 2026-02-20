"""
Session handoff tools for Archon MCP Server.

Enables agents to create, accept, complete, reject, and query session
handoffs — the mechanism for passing ongoing work between agents.
"""
import json
import logging
from urllib.parse import urljoin

import httpx
from mcp.server.fastmcp import Context, FastMCP

from src.mcp_server.utils.error_handling import MCPErrorFormatter
from src.mcp_server.utils.timeout_config import get_default_timeout
from src.server.config.service_discovery import get_api_url

logger = logging.getLogger(__name__)


def register_handoff_tools(mcp: FastMCP):
    """Register session handoff tools with the MCP server."""

    @mcp.tool()
    async def find_handoffs(
        ctx: Context,
        action: str = "list",
        handoff_id: str | None = None,
        agent: str | None = None,
        session_id: str | None = None,
        status: str | None = None,
    ) -> str:
        """
        Find session handoffs (list, get by ID, or get pending for an agent).

        Actions:
        - "list": List handoffs with optional filters
        - "get": Get a specific handoff by ID
        - "pending": Get all pending handoffs addressed to an agent

        Args:
            action: "list", "get", or "pending"
            handoff_id: Handoff UUID (required for "get")
            agent: Agent name — used as to_agent filter for "list" and required for "pending"
            session_id: Filter by session UUID for "list"
            status: Filter by status for "list" (pending, accepted, completed, rejected)

        Returns:
            JSON with handoff(s) data
        """
        try:
            api_url = get_api_url()
            timeout = get_default_timeout()

            async with httpx.AsyncClient(timeout=timeout) as client:

                if action == "get":
                    if not handoff_id:
                        return json.dumps({"success": False, "error": "get requires: handoff_id"})
                    response = await client.get(urljoin(api_url, f"/api/handoffs/{handoff_id}"))
                    if response.status_code == 200:
                        return json.dumps({"success": True, "handoff": response.json()["handoff"]})
                    else:
                        return MCPErrorFormatter.from_http_error(response, "get handoff")

                elif action == "pending":
                    if not agent:
                        return json.dumps({"success": False, "error": "pending requires: agent"})
                    response = await client.get(urljoin(api_url, f"/api/handoffs/pending/{agent}"))
                    if response.status_code == 200:
                        result = response.json()
                        return json.dumps({
                            "success": True,
                            "handoffs": result["handoffs"],
                            "count": result["count"],
                        })
                    else:
                        return MCPErrorFormatter.from_http_error(response, "get pending handoffs")

                elif action == "list":
                    params = {}
                    if session_id:
                        params["session_id"] = session_id
                    if agent:
                        params["agent"] = agent
                    if status:
                        params["status"] = status
                    response = await client.get(urljoin(api_url, "/api/handoffs"), params=params)
                    if response.status_code == 200:
                        result = response.json()
                        return json.dumps({
                            "success": True,
                            "handoffs": result["handoffs"],
                            "count": result["count"],
                        })
                    else:
                        return MCPErrorFormatter.from_http_error(response, "list handoffs")

                else:
                    return json.dumps({
                        "success": False,
                        "error": f"Unknown action '{action}'. Valid actions: list, get, pending",
                    })

        except Exception as e:
            return MCPErrorFormatter.from_exception(e, "find handoffs")

    @mcp.tool()
    async def manage_handoff(
        ctx: Context,
        action: str,
        handoff_id: str | None = None,
        session_id: str | None = None,
        from_agent: str | None = None,
        to_agent: str | None = None,
        context: dict | None = None,
        notes: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        """
        Manage session handoffs (create, accept, complete, or reject).

        Actions:
        - "create": Create a new pending handoff
        - "accept": Accept a pending handoff (sets accepted_at)
        - "complete": Complete an accepted handoff (sets completed_at)
        - "reject": Reject a pending handoff

        Args (create):
            session_id: UUID of the session being handed off
            from_agent: Agent initiating the handoff
            to_agent: Agent that should receive the work
            context: Structured context payload
            notes: Free-text instructions for the receiving agent
            metadata: Additional metadata

        Args (accept/complete/reject):
            handoff_id: UUID of the handoff to update

        Returns:
            JSON with handoff data
        """
        try:
            api_url = get_api_url()
            timeout = get_default_timeout()

            async with httpx.AsyncClient(timeout=timeout) as client:

                if action == "create":
                    if not all([session_id, from_agent, to_agent]):
                        return json.dumps({
                            "success": False,
                            "error": "create requires: session_id, from_agent, to_agent",
                        })
                    response = await client.post(
                        urljoin(api_url, "/api/handoffs"),
                        json={
                            "session_id": session_id,
                            "from_agent": from_agent,
                            "to_agent": to_agent,
                            "context": context or {},
                            "notes": notes,
                            "metadata": metadata or {},
                        },
                    )
                    if response.status_code == 200:
                        return json.dumps({"success": True, "handoff": response.json()["handoff"]})
                    else:
                        return MCPErrorFormatter.from_http_error(response, "create handoff")

                elif action in ("accept", "complete", "reject"):
                    if not handoff_id:
                        return json.dumps({
                            "success": False,
                            "error": f"{action} requires: handoff_id",
                        })
                    response = await client.post(
                        urljoin(api_url, f"/api/handoffs/{handoff_id}/{action}")
                    )
                    if response.status_code == 200:
                        return json.dumps({"success": True, "handoff": response.json()["handoff"]})
                    else:
                        return MCPErrorFormatter.from_http_error(response, f"{action} handoff")

                else:
                    return json.dumps({
                        "success": False,
                        "error": f"Unknown action '{action}'. Valid actions: create, accept, complete, reject",
                    })

        except Exception as e:
            return MCPErrorFormatter.from_exception(e, "manage handoff")
