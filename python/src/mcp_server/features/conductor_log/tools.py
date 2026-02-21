"""
Conductor Log MCP tools for Archon.

These tools are designed to be called by the Conductor agent (Claude or Gemini)
during orchestration. They allow the Conductor to persist its internal delegation
reasoning so the swarm has a transparent, queryable record of every delegation
decision — why an agent was chosen, what context was injected, and what happened.

Typical usage flow:
  1. Conductor decides to delegate a task.
  2. Conductor calls log_conductor_reasoning() immediately — before execution.
  3. Sub-agent executes the delegated work.
  4. Conductor (or Work Order executor) calls update_delegation_outcome() with result.
  5. Any agent can call get_work_order_reasoning() to review delegation history.
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


def register_conductor_log_tools(mcp: FastMCP):
    """Register conductor log tools with the MCP server."""

    @mcp.tool()
    async def log_conductor_reasoning(
        ctx: Context,
        work_order_id: str,
        conductor_agent: str,
        delegation_target: str,
        reasoning: str,
        context_injected: dict[str, Any] | None = None,
        decision_factors: list[Any] | None = None,
        confidence_score: float | None = None,
        mission_id: str | None = None,
    ) -> str:
        """
        Record the Conductor's reasoning for a delegation decision.

        Call this tool immediately after deciding which sub-agent to delegate to,
        and before the sub-agent is actually invoked. This ensures the reasoning
        is captured regardless of whether execution succeeds or fails.

        The entry is created with outcome=null. Use update_delegation_outcome()
        once the delegated task completes.

        Args:
            work_order_id: The Work Order ID this delegation belongs to.
            conductor_agent: Which agent is acting as Conductor (e.g. "claude", "gemini").
            delegation_target: Which sub-agent type was selected (e.g. "claude_code",
                               "gemini_pro", "gpt4", "human").
            reasoning: Full natural-language explanation of why this delegation was chosen.
                       Include agent capability reasoning, task fit, load considerations, etc.
            context_injected: Optional dict describing which context slices were injected
                              into the sub-agent's prompt (e.g. {"kb_docs": 3, "session": "uuid"}).
            decision_factors: Optional list of factors that drove the decision
                              (e.g. ["requires_code_execution", "low_latency_needed", "claude_code_specialized"]).
            confidence_score: Self-reported confidence in this delegation (0.0–1.0).
                              Use 1.0 for highly certain decisions, lower for ambiguous ones.
            mission_id: Optional mission or parent task identifier for grouping
                        multiple related work orders under one mission.

        Returns:
            JSON with the created log entry including its UUID (needed for update_delegation_outcome).

        Example:
            log_conductor_reasoning(
                work_order_id="WO-20260221-001",
                conductor_agent="claude",
                delegation_target="claude_code",
                reasoning="Task requires file system access and running tests. Claude Code is the only agent with terminal access and can execute pytest directly.",
                context_injected={"work_order": "WO-20260221-001", "kb_docs": 2},
                decision_factors=["requires_terminal_access", "test_execution", "file_system_writes"],
                confidence_score=0.95,
                mission_id="phase3_orchestration"
            )
        """
        try:
            api_url = get_api_url()
            timeout = get_default_timeout()

            payload: dict[str, Any] = {
                "work_order_id": work_order_id,
                "conductor_agent": conductor_agent,
                "delegation_target": delegation_target,
                "reasoning": reasoning,
            }
            if context_injected is not None:
                payload["context_injected"] = context_injected
            if decision_factors is not None:
                payload["decision_factors"] = decision_factors
            if confidence_score is not None:
                payload["confidence_score"] = confidence_score
            if mission_id is not None:
                payload["mission_id"] = mission_id

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    urljoin(api_url, "/api/conductor-log"),
                    json=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    return json.dumps({
                        "success": True,
                        "entry": result["entry"],
                        "log_id": result["entry"]["id"],
                    })
                else:
                    return MCPErrorFormatter.format_http_error(response)

        except httpx.TimeoutException:
            return MCPErrorFormatter.format_timeout_error("Conductor log creation timed out")
        except Exception as e:
            return MCPErrorFormatter.format_generic_error(
                f"Failed to log conductor reasoning: {str(e)}"
            )

    @mcp.tool()
    async def update_delegation_outcome(
        ctx: Context,
        log_id: str,
        outcome: str,
        outcome_notes: str | None = None,
    ) -> str:
        """
        Update the outcome of a delegation after the sub-agent finishes.

        Call this tool once the delegated task has completed (succeeded, failed,
        or partially succeeded). This closes the loop on the reasoning entry
        created by log_conductor_reasoning() and enables success-rate analytics.

        Args:
            log_id: UUID of the conductor log entry to update (returned by
                    log_conductor_reasoning as "log_id").
            outcome: Execution result — must be one of:
                     "success"  — sub-agent completed the task as expected
                     "failure"  — sub-agent failed to complete the task
                     "partial"  — sub-agent completed part of the task
            outcome_notes: Optional free-text notes on the outcome. Useful for:
                           - Error messages or stack traces on failure
                           - What partial work was completed
                           - Lessons learned for future delegation decisions

        Returns:
            JSON with the updated log entry.

        Example:
            update_delegation_outcome(
                log_id="550e8400-e29b-41d4-a716-446655440000",
                outcome="success",
                outcome_notes="All 12 tests passed. Migration applied cleanly."
            )

            update_delegation_outcome(
                log_id="550e8400-e29b-41d4-a716-446655440000",
                outcome="partial",
                outcome_notes="8/12 tests passed. 4 failed due to missing env var SUPABASE_URL."
            )
        """
        if outcome not in ("success", "failure", "partial"):
            return json.dumps({
                "success": False,
                "error": f"Invalid outcome: '{outcome}'. Must be 'success', 'failure', or 'partial'."
            })

        try:
            api_url = get_api_url()
            timeout = get_default_timeout()

            payload: dict[str, Any] = {"outcome": outcome}
            if outcome_notes is not None:
                payload["outcome_notes"] = outcome_notes

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.patch(
                    urljoin(api_url, f"/api/conductor-log/{log_id}/outcome"),
                    json=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    return json.dumps({
                        "success": True,
                        "entry": result["entry"],
                    })
                elif response.status_code == 404:
                    return json.dumps({
                        "success": False,
                        "error": f"Conductor log entry {log_id} not found"
                    })
                else:
                    return MCPErrorFormatter.format_http_error(response)

        except httpx.TimeoutException:
            return MCPErrorFormatter.format_timeout_error("Outcome update timed out")
        except Exception as e:
            return MCPErrorFormatter.format_generic_error(
                f"Failed to update delegation outcome: {str(e)}"
            )

    @mcp.tool()
    async def get_work_order_reasoning(
        ctx: Context,
        work_order_id: str,
    ) -> str:
        """
        Retrieve all conductor reasoning entries for a work order.

        Use this tool to review the full delegation history of a work order —
        who delegated what, why, with what confidence, and what the outcomes were.
        Useful for:
        - Post-mortem analysis after a work order completes or fails
        - Resuming orchestration after an interruption
        - Auditing delegation decisions made by another Conductor agent

        Args:
            work_order_id: The Work Order ID to retrieve delegation history for.

        Returns:
            JSON with all reasoning entries for the work order, in chronological order,
            plus a summary of total delegations and outcomes.

        Example:
            get_work_order_reasoning(work_order_id="WO-20260221-001")
        """
        try:
            api_url = get_api_url()
            timeout = get_default_timeout()

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(
                    urljoin(api_url, f"/api/conductor-log/work-order/{work_order_id}")
                )

                if response.status_code == 200:
                    result = response.json()
                    entries = result.get("entries", [])

                    # Build a lightweight outcome summary for quick Conductor orientation
                    outcomes = [e.get("outcome") for e in entries]
                    summary = {
                        "total": len(entries),
                        "success": outcomes.count("success"),
                        "failure": outcomes.count("failure"),
                        "partial": outcomes.count("partial"),
                        "pending": outcomes.count(None),
                    }

                    return json.dumps({
                        "success": True,
                        "work_order_id": work_order_id,
                        "entries": entries,
                        "outcome_summary": summary,
                    })
                else:
                    return MCPErrorFormatter.format_http_error(response)

        except httpx.TimeoutException:
            return MCPErrorFormatter.format_timeout_error("Work order reasoning retrieval timed out")
        except Exception as e:
            return MCPErrorFormatter.format_generic_error(
                f"Failed to retrieve work order reasoning: {str(e)}"
            )
