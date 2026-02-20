"""
Shared context tools for Archon MCP Server.

Allows agents to read, write, and inspect the shared context board —
a key/value store visible to all agents in the ecosystem.
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


def register_context_tools(mcp: FastMCP):
    """Register shared context tools with the MCP server."""

    @mcp.tool()
    async def find_context(
        ctx: Context,
        action: str = "list",
        key: str | None = None,
        prefix: str | None = None,
        limit: int = 20,
    ) -> str:
        """
        Find entries on the shared context board (list, get, or history).

        Actions:
        - "list": List all context entries, optionally filtered by key prefix
        - "get": Get a specific context entry by key
        - "history": Get the change history for a key

        Args:
            action: "list", "get", or "history"
            key: Context key (required for "get" and "history")
            prefix: Key prefix filter for "list" (e.g. "project/")
            limit: Max history records for "history" (default: 20)

        Returns:
            JSON with context data
        """
        try:
            api_url = get_api_url()
            timeout = get_default_timeout()

            async with httpx.AsyncClient(timeout=timeout) as client:

                if action == "get":
                    if not key:
                        return json.dumps({"success": False, "error": "get requires: key"})
                    response = await client.get(urljoin(api_url, f"/api/context/{key}"))
                    if response.status_code == 200:
                        return json.dumps({"success": True, "context": response.json()["context"]})
                    else:
                        return MCPErrorFormatter.from_http_error(response, "get context")

                elif action == "history":
                    if not key:
                        return json.dumps({"success": False, "error": "history requires: key"})
                    response = await client.get(
                        urljoin(api_url, f"/api/context/{key}/history"),
                        params={"limit": limit},
                    )
                    if response.status_code == 200:
                        result = response.json()
                        return json.dumps({
                            "success": True,
                            "history": result["history"],
                            "count": result["count"],
                        })
                    else:
                        return MCPErrorFormatter.from_http_error(response, "get context history")

                elif action == "list":
                    params = {}
                    if prefix:
                        params["prefix"] = prefix
                    response = await client.get(urljoin(api_url, "/api/context"), params=params)
                    if response.status_code == 200:
                        result = response.json()
                        return json.dumps({
                            "success": True,
                            "context": result["context"],
                            "count": result["count"],
                        })
                    else:
                        return MCPErrorFormatter.from_http_error(response, "list context")

                else:
                    return json.dumps({
                        "success": False,
                        "error": f"Unknown action '{action}'. Valid actions: list, get, history",
                    })

        except Exception as e:
            return MCPErrorFormatter.from_exception(e, "find context")

    @mcp.tool()
    async def manage_context(
        ctx: Context,
        action: str,
        key: str,
        set_by: str = "mcp",
        value: Any | None = None,
        session_id: str | None = None,
        expires_at: str | None = None,
    ) -> str:
        """
        Manage entries on the shared context board (set or delete).

        Actions:
        - "set": Create or update a context entry
        - "delete": Remove a context entry

        Args:
            action: "set" or "delete"
            key: Context key (required for all actions)
            set_by: Agent or user writing the value (default: mcp)
            value: JSON-serialisable value (required for "set")
            session_id: Optional linked session UUID (set only)
            expires_at: Optional ISO-8601 expiry timestamp (set only)

        Returns:
            JSON with result
        """
        try:
            api_url = get_api_url()
            timeout = get_default_timeout()

            async with httpx.AsyncClient(timeout=timeout) as client:

                if action == "set":
                    if value is None:
                        return json.dumps({"success": False, "error": "set requires: value"})
                    payload: dict = {"value": value, "set_by": set_by}
                    if session_id:
                        payload["session_id"] = session_id
                    if expires_at:
                        payload["expires_at"] = expires_at
                    response = await client.put(
                        urljoin(api_url, f"/api/context/{key}"),
                        json=payload,
                    )
                    if response.status_code == 200:
                        return json.dumps({"success": True, "context": response.json()["context"]})
                    else:
                        return MCPErrorFormatter.from_http_error(response, "set context")

                elif action == "delete":
                    response = await client.delete(urljoin(api_url, f"/api/context/{key}"))
                    if response.status_code == 200:
                        return json.dumps({"success": True, "deleted": key})
                    else:
                        return MCPErrorFormatter.from_http_error(response, "delete context")

                else:
                    return json.dumps({
                        "success": False,
                        "error": f"Unknown action '{action}'. Valid actions: set, delete",
                    })

        except Exception as e:
            return MCPErrorFormatter.from_exception(e, "manage context")
