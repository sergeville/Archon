"""
Pattern management tools for Archon MCP Server.

Provides access to learned behavioral and technical patterns, enabling agents
to harvest 'wisdom' from experiences and search for relevant patterns.
"""
import json
import logging
from typing import Any, Optional
from urllib.parse import urljoin

import httpx
from mcp.server.fastmcp import Context, FastMCP

from src.mcp_server.utils.error_handling import MCPErrorFormatter
from src.mcp_server.utils.timeout_config import get_default_timeout
from src.server.config.service_discovery import get_api_url

logger = logging.getLogger(__name__)

MAX_DESCRIPTION_LENGTH = 1000
DEFAULT_PAGE_SIZE = 10


def truncate_text(text: str, max_length: int = MAX_DESCRIPTION_LENGTH) -> str:
    """Truncate text to maximum length with ellipsis."""
    if text and len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text


def optimize_pattern_response(pattern: dict) -> dict:
    """Trim large fields for MCP response."""
    pattern = pattern.copy()
    if "description" in pattern and pattern["description"]:
        pattern["description"] = truncate_text(pattern["description"])
    if "action" in pattern and pattern["action"]:
        pattern["action"] = truncate_text(pattern["action"])
    # Drop raw embedding vector — it's large and not useful in MCP responses
    pattern.pop("embedding", None)
    return pattern


def register_pattern_tools(mcp: FastMCP):
    """Register pattern management tools with the MCP server."""

    @mcp.tool()
    async def find_patterns(
        ctx: Context,
        pattern_id: Optional[str] = None,
        query: Optional[str] = None,
        pattern_type: Optional[str] = None,
        domain: Optional[str] = None,
        limit: int = DEFAULT_PAGE_SIZE,
        threshold: float = 0.7,
    ) -> str:
        """
        Find patterns (consolidated: list + get by ID + semantic search).

        Modes:
        - pattern_id: Get full details for a specific pattern
        - query: Semantic search for patterns similar to the query text
        - No args / type/domain only: List patterns with optional filters

        Args:
            pattern_id: UUID of a specific pattern to retrieve
            query: Semantic search query (requires embedding service)
            pattern_type: Filter by type (success, failure, technical, process)
            domain: Filter by application domain
            limit: Maximum results (default: 10)
            threshold: Minimum similarity for semantic search (0-1, default: 0.7)

        Returns:
            JSON with pattern(s) and metadata
        """
        try:
            api_url = get_api_url()
            timeout = get_default_timeout()

            async with httpx.AsyncClient(timeout=timeout) as client:

                # Get single pattern by ID
                if pattern_id:
                    response = await client.get(
                        urljoin(api_url, f"/api/patterns/{pattern_id}")
                    )
                    if response.status_code == 200:
                        result = response.json()
                        pattern = optimize_pattern_response(result["pattern"])
                        return json.dumps({"success": True, "pattern": pattern})
                    else:
                        return MCPErrorFormatter.from_http_error(response, "get pattern")

                # Semantic search
                if query:
                    response = await client.post(
                        urljoin(api_url, "/api/patterns/search"),
                        json={
                            "query": query,
                            "limit": limit,
                            "threshold": threshold,
                            "domain": domain
                        }
                    )
                    if response.status_code == 200:
                        result = response.json()
                        patterns = [optimize_pattern_response(p) for p in result.get("patterns", [])]
                        return json.dumps({
                            "success": True,
                            "patterns": patterns,
                            "count": len(patterns),
                            "mode": "semantic_search"
                        })
                    else:
                        return MCPErrorFormatter.from_http_error(response, "search patterns")

                # List with optional filters
                params = {"limit": limit}
                if pattern_type:
                    params["pattern_type"] = pattern_type
                if domain:
                    params["domain"] = domain

                response = await client.get(
                    urljoin(api_url, "/api/patterns"),
                    params=params
                )
                if response.status_code == 200:
                    result = response.json()
                    patterns = [optimize_pattern_response(p) for p in result.get("patterns", [])]
                    return json.dumps({
                        "success": True,
                        "patterns": patterns,
                        "count": len(patterns),
                        "mode": "list"
                    })
                else:
                    return MCPErrorFormatter.from_http_error(response, "list patterns")

        except Exception as e:
            return MCPErrorFormatter.from_exception(e, "find patterns")

    @mcp.tool()
    async def manage_pattern(
        ctx: Context,
        action: str,
        # harvest fields
        pattern_type: Optional[str] = None,
        domain: Optional[str] = None,
        description: Optional[str] = None,
        action_text: Optional[str] = None,
        outcome: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
        created_by: str = "mcp",
        # observation fields
        pattern_id: Optional[str] = None,
        session_id: Optional[str] = None,
        success_rating: Optional[int] = None,
        feedback: Optional[str] = None,
    ) -> str:
        """
        Manage patterns (consolidated: harvest + record_observation).

        Actions:
        - "harvest": Save a new learned pattern to shared memory
        - "record_observation": Record that a pattern was applied and rate its effectiveness

        Args (harvest):
            pattern_type: Type of pattern (success, failure, technical, process)
            domain: Application domain (e.g., database, api, development)
            description: What the pattern is about
            action_text: The core reusable action
            outcome: Result when the action was applied
            context: Environmental context (optional)
            metadata: Additional metadata (optional)
            created_by: Agent identifier (default: mcp)

        Args (record_observation):
            pattern_id: UUID of the pattern that was applied
            session_id: Current session UUID (optional)
            success_rating: Effectiveness rating 1-5 (5 = very effective)
            feedback: Notes about how it went

        Returns:
            JSON with created pattern or observation
        """
        try:
            api_url = get_api_url()
            timeout = get_default_timeout()

            async with httpx.AsyncClient(timeout=timeout) as client:

                if action == "harvest":
                    if not all([pattern_type, domain, description, action_text]):
                        return json.dumps({
                            "success": False,
                            "error": "harvest requires: pattern_type, domain, description, action_text"
                        })
                    response = await client.post(
                        urljoin(api_url, "/api/patterns"),
                        json={
                            "pattern_type": pattern_type,
                            "domain": domain,
                            "description": description,
                            "action": action_text,
                            "outcome": outcome,
                            "context": context,
                            "metadata": metadata,
                            "created_by": created_by
                        }
                    )
                    if response.status_code == 200:
                        result = response.json()
                        pattern = optimize_pattern_response(result["pattern"])
                        return json.dumps({"success": True, "pattern": pattern})
                    else:
                        return MCPErrorFormatter.from_http_error(response, "harvest pattern")

                elif action == "record_observation":
                    if not pattern_id:
                        return json.dumps({
                            "success": False,
                            "error": "record_observation requires: pattern_id"
                        })
                    response = await client.post(
                        urljoin(api_url, "/api/patterns/observations"),
                        json={
                            "pattern_id": pattern_id,
                            "session_id": session_id,
                            "success_rating": success_rating,
                            "feedback": feedback,
                        }
                    )
                    if response.status_code == 200:
                        result = response.json()
                        return json.dumps({"success": True, "observation": result["observation"]})
                    else:
                        return MCPErrorFormatter.from_http_error(response, "record observation")

                else:
                    return json.dumps({
                        "success": False,
                        "error": f"Unknown action '{action}'. Valid actions: harvest, record_observation"
                    })

        except Exception as e:
            return MCPErrorFormatter.from_exception(e, "manage pattern")
