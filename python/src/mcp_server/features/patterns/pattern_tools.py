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

# Optimization constants
MAX_DESCRIPTION_LENGTH = 1000
DEFAULT_PAGE_SIZE = 10


def truncate_text(text: str, max_length: int = MAX_DESCRIPTION_LENGTH) -> str:
    """Truncate text to maximum length with ellipsis."""
    if text and len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text


def optimize_pattern_response(pattern: dict) -> dict:
    """Optimize pattern object for MCP response."""
    pattern = pattern.copy()
    if "description" in pattern and pattern["description"]:
        pattern["description"] = truncate_text(pattern["description"])
    if "action" in pattern and pattern["action"]:
        pattern["action"] = truncate_text(pattern["action"])
    return pattern


def register_pattern_tools(mcp: FastMCP):
    """Register pattern management tools with the MCP server."""

    @mcp.tool()
    async def harvest_pattern(
        ctx: Context,
        pattern_type: str,
        domain: str,
        description: str,
        action: str,
        outcome: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
        created_by: str = "mcp"
    ) -> str:
        """
        Save a learned pattern to the shared memory system.

        Patterns are sequences of actions/decisions that led to a specific outcome.
        Use this when you identify a reusable strategy or a 'lesson learned'.

        Args:
            pattern_type: Type (success, failure, technical, process)
            domain: Application domain
            description: What the pattern is about
            action: Core reusable action
            outcome: Result of the action
            context: Context when pattern was seen
            metadata: Additional metadata
            created_by: Agent identifier

        Returns:
            JSON with created pattern
        """
        try:
            api_url = get_api_url()
            timeout = get_default_timeout()

            payload = {
                "pattern_type": pattern_type,
                "domain": domain,
                "description": description,
                "action": action,
                "outcome": outcome,
                "context": context,
                "metadata": metadata,
                "created_by": created_by
            }

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    urljoin(api_url, "/api/patterns"),
                    json=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    return json.dumps({"success": True, "pattern": result["pattern"]})
                else:
                    return MCPErrorFormatter.format_http_error(response)

        except Exception as e:
            return MCPErrorFormatter.format_generic_error(f"Failed to harvest pattern: {str(e)}")

    @mcp.tool()
    async def search_patterns(
        ctx: Context,
        query: str,
        limit: int = 10,
        threshold: float = 0.7,
        domain: Optional[str] = None
    ) -> str:
        """
        Search for reusable patterns semantically.

        Finds patterns similar to the query, optionally filtered by domain.
        Use this before starting a new type of task to see how others did it.

        Args:
            query: Search query
            limit: Results limit
            threshold: Similarity threshold (0-1)
            domain: Domain filter

        Returns:
            JSON array of matching patterns
        """
        try:
            api_url = get_api_url()
            timeout = get_default_timeout()

            payload = {
                "query": query,
                "limit": limit,
                "threshold": threshold,
                "domain": domain
            }

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    urljoin(api_url, "/api/patterns/search"),
                    json=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    patterns = result.get("patterns", [])
                    optimized = [optimize_pattern_response(p) for p in patterns]
                    return json.dumps({"success": True, "patterns": optimized})
                else:
                    return MCPErrorFormatter.format_http_error(response)

        except Exception as e:
            return MCPErrorFormatter.format_generic_error(f"Failed to search patterns: {str(e)}")

    @mcp.tool()
    async def record_pattern_observation(
        ctx: Context,
        pattern_id: str,
        session_id: Optional[str] = None,
        success_rating: Optional[int] = None,
        feedback: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> str:
        """
        Record when a pattern is applied or observed again.

        Args:
            pattern_id: Pattern UUID
            session_id: Current session UUID
            success_rating: 1-5 rating of pattern effectiveness
            feedback: Human/AI feedback on application
            metadata: Additional metadata

        Returns:
            JSON with observation record
        """
        try:
            api_url = get_api_url()
            timeout = get_default_timeout()

            payload = {
                "pattern_id": pattern_id,
                "session_id": session_id,
                "success_rating": success_rating,
                "feedback": feedback,
                "metadata": metadata
            }

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    urljoin(api_url, "/api/patterns/observations"),
                    json=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    return json.dumps({"success": True, "observation": result["observation"]})
                else:
                    return MCPErrorFormatter.format_http_error(response)

        except Exception as e:
            return MCPErrorFormatter.format_generic_error(f"Failed to record observation: {str(e)}")
