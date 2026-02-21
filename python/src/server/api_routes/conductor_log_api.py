"""
Conductor Log API endpoints for Archon

Handles:
- Creating delegation reasoning entries (one per Conductor delegation)
- Retrieving entries by log ID or by work order
- Updating delegation outcome after execution completes
- Aggregate stats across conductors and delegation targets
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi import status as http_status
from pydantic import BaseModel, Field

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)

router = APIRouter(prefix="/api/conductor-log", tags=["conductor-log"])


# =====================================================
# Request / Response Models
# =====================================================


class CreateConductorLogRequest(BaseModel):
    work_order_id: str
    mission_id: str | None = None
    conductor_agent: str
    delegation_target: str
    reasoning: str
    context_injected: dict[str, Any] | None = None
    decision_factors: list[Any] | None = None
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)


class UpdateOutcomeRequest(BaseModel):
    outcome: str = Field(..., pattern="^(success|failure|partial)$")
    outcome_notes: str | None = None


class ConductorLogEntry(BaseModel):
    id: str
    work_order_id: str
    mission_id: str | None
    conductor_agent: str
    delegation_target: str
    reasoning: str
    context_injected: dict[str, Any]
    decision_factors: list[Any]
    confidence_score: float | None
    outcome: str | None
    outcome_notes: str | None
    created_at: str
    updated_at: str


# =====================================================
# Endpoints
# =====================================================


@router.post("")
async def create_conductor_log(request: CreateConductorLogRequest):
    """
    Create a new conductor reasoning entry.

    Called by the Conductor immediately after deciding on a delegation —
    before the sub-agent is actually invoked — so the reasoning is captured
    regardless of whether execution succeeds.
    """
    try:
        client = get_supabase_client()

        payload: dict[str, Any] = {
            "work_order_id": request.work_order_id,
            "conductor_agent": request.conductor_agent,
            "delegation_target": request.delegation_target,
            "reasoning": request.reasoning,
            "context_injected": request.context_injected or {},
            "decision_factors": request.decision_factors or [],
        }
        if request.mission_id is not None:
            payload["mission_id"] = request.mission_id
        if request.confidence_score is not None:
            payload["confidence_score"] = request.confidence_score

        response = client.table("conductor_reasoning_log").insert(payload).execute()

        if not response.data:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Insert returned no data"
            )

        entry = response.data[0]
        logger.info(
            f"Conductor log created: {entry['id']} "
            f"(work_order={request.work_order_id}, target={request.delegation_target})"
        )
        return {
            "message": "Conductor log entry created successfully",
            "entry": entry
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating conductor log entry: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create conductor log entry: {str(e)}"
        )


@router.get("/stats")
async def get_conductor_stats():
    """
    Aggregate delegation statistics across all conductors.

    Returns per-conductor-and-target breakdowns including:
    - Total delegations
    - Average confidence score
    - Success / failure / partial / pending counts
    - Success rate percentage
    """
    try:
        client = get_supabase_client()

        response = (
            client.table("conductor_reasoning_log")
            .select(
                "conductor_agent, delegation_target, confidence_score, outcome"
            )
            .execute()
        )

        rows = response.data or []

        # Aggregate in Python — the SQL view is available for direct DB access;
        # here we keep the computation in the API layer for consistency with the
        # rest of the codebase which avoids raw SQL in API routes.
        stats: dict[str, dict] = {}
        for row in rows:
            key = f"{row['conductor_agent']}::{row['delegation_target']}"
            if key not in stats:
                stats[key] = {
                    "conductor_agent": row["conductor_agent"],
                    "delegation_target": row["delegation_target"],
                    "total_delegations": 0,
                    "confidence_scores": [],
                    "successes": 0,
                    "failures": 0,
                    "partials": 0,
                    "pending": 0,
                }
            entry = stats[key]
            entry["total_delegations"] += 1
            if row["confidence_score"] is not None:
                entry["confidence_scores"].append(row["confidence_score"])
            outcome = row.get("outcome")
            if outcome == "success":
                entry["successes"] += 1
            elif outcome == "failure":
                entry["failures"] += 1
            elif outcome == "partial":
                entry["partials"] += 1
            else:
                entry["pending"] += 1

        result = []
        for entry in stats.values():
            scores = entry.pop("confidence_scores")
            decided = entry["successes"] + entry["failures"] + entry["partials"]
            entry["avg_confidence"] = round(sum(scores) / len(scores), 3) if scores else None
            entry["success_rate_pct"] = (
                round(entry["successes"] / decided * 100, 1) if decided else None
            )
            result.append(entry)

        result.sort(key=lambda x: (-x["total_delegations"], x["conductor_agent"]))

        return {
            "stats": result,
            "total_entries": len(rows),
            "total_conductor_target_pairs": len(result),
        }

    except Exception as e:
        logger.error(f"Error fetching conductor stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch conductor stats: {str(e)}"
        )


@router.get("/work-order/{work_order_id}")
async def get_logs_for_work_order(work_order_id: str):
    """
    Get all conductor reasoning entries for a specific work order.

    Returns entries in chronological order, giving a full delegation
    history for the work order.
    """
    try:
        client = get_supabase_client()

        response = (
            client.table("conductor_reasoning_log")
            .select("*")
            .eq("work_order_id", work_order_id)
            .order("created_at", desc=False)
            .execute()
        )

        entries = response.data or []
        return {
            "work_order_id": work_order_id,
            "entries": entries,
            "total": len(entries),
        }

    except Exception as e:
        logger.error(f"Error fetching logs for work order {work_order_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch conductor logs: {str(e)}"
        )


@router.get("/{log_id}")
async def get_conductor_log(log_id: str):
    """Get a single conductor reasoning entry by its UUID."""
    try:
        client = get_supabase_client()

        response = (
            client.table("conductor_reasoning_log")
            .select("*")
            .eq("id", log_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Conductor log entry {log_id} not found"
            )

        return {"entry": response.data[0]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conductor log {log_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch conductor log entry: {str(e)}"
        )


@router.patch("/{log_id}/outcome")
async def update_delegation_outcome(log_id: str, request: UpdateOutcomeRequest):
    """
    Update the outcome of a delegation after the sub-agent finishes.

    Called by the Conductor (or the Work Order executor) once the delegated
    task has completed. Fills in the outcome and optional notes fields that
    were left null at creation time.
    """
    try:
        client = get_supabase_client()

        payload: dict[str, Any] = {"outcome": request.outcome}
        if request.outcome_notes is not None:
            payload["outcome_notes"] = request.outcome_notes

        response = (
            client.table("conductor_reasoning_log")
            .update(payload)
            .eq("id", log_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Conductor log entry {log_id} not found"
            )

        entry = response.data[0]
        logger.info(f"Conductor log {log_id} outcome updated to: {request.outcome}")
        return {
            "message": "Outcome updated successfully",
            "entry": entry
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating outcome for log {log_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update outcome: {str(e)}"
        )
