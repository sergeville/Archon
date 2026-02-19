"""
Agent registry tools for Archon MCP Server.

Allows agents to register themselves, discover other agents, send heartbeats,
and deactivate agents that are no longer active.
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


def register_agent_tools(mcp: FastMCP):
    """Register agent registry tools with the MCP server."""

    @mcp.tool()
    async def find_agents(
        ctx: Context,
        action: str = "list",
        name: str | None = None,
        status: str | None = None,
    ) -> str:
        """
        Find agents in the registry (list or get by name).

        Actions:
        - "list": List all registered agents, optionally filtered by status
        - "get": Get details for a specific agent by name

        Args:
            action: "list" or "get"
            name: Agent name (required for "get")
            status: Filter by status for "list" — "active", "inactive", or "busy"

        Returns:
            JSON with agent(s) data
        """
        try:
            api_url = get_api_url()
            timeout = get_default_timeout()

            async with httpx.AsyncClient(timeout=timeout) as client:

                if action == "get":
                    if not name:
                        return json.dumps({"success": False, "error": "get requires: name"})
                    response = await client.get(urljoin(api_url, f"/api/agents/{name}"))
                    if response.status_code == 200:
                        return json.dumps({"success": True, "agent": response.json()["agent"]})
                    else:
                        return MCPErrorFormatter.from_http_error(response, "get agent")

                elif action == "list":
                    params = {}
                    if status:
                        params["status"] = status
                    response = await client.get(urljoin(api_url, "/api/agents"), params=params)
                    if response.status_code == 200:
                        result = response.json()
                        return json.dumps({
                            "success": True,
                            "agents": result["agents"],
                            "count": result["count"],
                        })
                    else:
                        return MCPErrorFormatter.from_http_error(response, "list agents")

                else:
                    return json.dumps({
                        "success": False,
                        "error": f"Unknown action '{action}'. Valid actions: list, get",
                    })

        except Exception as e:
            return MCPErrorFormatter.from_exception(e, "find agents")

    @mcp.tool()
    async def manage_agent(
        ctx: Context,
        action: str,
        name: str,
        capabilities: list | None = None,
        metadata: dict | None = None,
    ) -> str:
        """
        Manage agents in the registry (register, heartbeat, or deactivate).

        Actions:
        - "register": Register or update an agent (upserts by name)
        - "heartbeat": Refresh last_seen and set status to active
        - "deactivate": Set agent status to inactive

        Args:
            action: "register", "heartbeat", or "deactivate"
            name: Agent name (required for all actions)
            capabilities: List of capability strings (register only)
            metadata: Additional metadata dict (register only)

        Returns:
            JSON with updated agent data
        """
        try:
            api_url = get_api_url()
            timeout = get_default_timeout()

            async with httpx.AsyncClient(timeout=timeout) as client:

                if action == "register":
                    response = await client.post(
                        urljoin(api_url, "/api/agents/register"),
                        json={
                            "name": name,
                            "capabilities": capabilities or [],
                            "metadata": metadata or {},
                        },
                    )
                    if response.status_code == 200:
                        return json.dumps({"success": True, "agent": response.json()["agent"]})
                    else:
                        return MCPErrorFormatter.from_http_error(response, "register agent")

                elif action == "heartbeat":
                    response = await client.post(
                        urljoin(api_url, f"/api/agents/{name}/heartbeat")
                    )
                    if response.status_code == 200:
                        return json.dumps({"success": True, "agent": response.json()["agent"]})
                    else:
                        return MCPErrorFormatter.from_http_error(response, "agent heartbeat")

                elif action == "deactivate":
                    response = await client.post(
                        urljoin(api_url, f"/api/agents/{name}/deactivate")
                    )
                    if response.status_code == 200:
                        return json.dumps({"success": True, "agent": response.json()["agent"]})
                    else:
                        return MCPErrorFormatter.from_http_error(response, "deactivate agent")

                else:
                    return json.dumps({
                        "success": False,
                        "error": f"Unknown action '{action}'. Valid actions: register, heartbeat, deactivate",
                    })

        except Exception as e:
            return MCPErrorFormatter.from_exception(e, "manage agent")
