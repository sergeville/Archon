"""
API routes for the Validation Council.

Risk-gating layer that evaluates Agent Work Orders before execution.
LOW/MED are auto-approved, HIGH is queued for human review,
DESTRUCTIVE is auto-blocked.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)
router = APIRouter(prefix="/api/council", tags=["Validation Council"])


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class EvaluateRequest(BaseModel):
    work_order_id: str
    risk_level: str = "LOW"  # LOW | MED | HIGH | DESTRUCTIVE
    user_request: str = ""


class EvaluateResponse(BaseModel):
    decision_id: str
    work_order_id: str
    decision: str  # approved | pending_human | blocked
    decided_by: str  # auto | human
    risk_level: str
    message: str


class ValidationDecision(BaseModel):
    id: str
    created_at: str
    work_order_id: str
    risk_level: str
    user_request_summary: str | None
    decision: str
    decided_by: str
    decided_at: str
    notes: str | None
    resolved_at: str | None


class ResolveRequest(BaseModel):
    notes: str | None = None


# ---------------------------------------------------------------------------
# Decision logic
# ---------------------------------------------------------------------------

_DECISION_MAP: dict[str, str] = {
    "LOW": "approved",
    "MED": "approved",
    "HIGH": "pending_human",
    "DESTRUCTIVE": "blocked",
}

_MESSAGE_MAP: dict[str, str] = {
    "approved": "Work order approved automatically.",
    "pending_human": "Work order queued for human review.",
    "blocked": "Work order blocked — destructive risk level.",
}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_work_order(request: EvaluateRequest):
    """Evaluate a work order and record the council decision."""
    try:
        level = request.risk_level.upper()
        decision = _DECISION_MAP.get(level)
        if decision is None:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid risk_level '{request.risk_level}'. Must be LOW, MED, HIGH, or DESTRUCTIVE.",
            )

        supabase = get_supabase_client()
        row = {
            "work_order_id": request.work_order_id,
            "risk_level": level,
            "user_request_summary": request.user_request or None,
            "decision": decision,
            "decided_by": "auto",
        }

        response = supabase.table("validation_council_decisions").insert(row).execute()
        if not response.data:
            raise Exception("Insert returned no data")

        entry = response.data[0]
        return EvaluateResponse(
            decision_id=entry["id"],
            work_order_id=entry["work_order_id"],
            decision=entry["decision"],
            decided_by=entry["decided_by"],
            risk_level=entry["risk_level"],
            message=_MESSAGE_MAP[decision],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating work order: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to evaluate work order: {str(e)}")


@router.get("/queue")
async def get_pending_queue(limit: int = Query(50, ge=1, le=500)):
    """Return decisions pending human review."""
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("validation_council_decisions")
            .select("*")
            .eq("decision", "pending_human")
            .is_("resolved_at", "null")
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )
        entries = response.data or []
        return {"entries": entries, "count": len(entries)}
    except Exception as e:
        logger.error(f"Error fetching pending queue: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch pending queue: {str(e)}")


@router.post("/queue/{decision_id}/approve")
async def approve_decision(decision_id: str, body: ResolveRequest):
    """Human-approve a pending decision."""
    try:
        supabase = get_supabase_client()
        now = datetime.now(timezone.utc).isoformat()
        update = {
            "decision": "approved",
            "decided_by": "human",
            "resolved_at": now,
        }
        if body.notes is not None:
            update["notes"] = body.notes

        response = (
            supabase.table("validation_council_decisions")
            .update(update)
            .eq("id", decision_id)
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=404, detail=f"Decision {decision_id} not found")

        return {"ok": True, "decision_id": decision_id, "resolved_at": now}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving decision {decision_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to approve decision: {str(e)}")


@router.post("/queue/{decision_id}/reject")
async def reject_decision(decision_id: str, body: ResolveRequest):
    """Human-reject a pending decision."""
    try:
        supabase = get_supabase_client()
        now = datetime.now(timezone.utc).isoformat()
        update = {
            "decision": "blocked",
            "decided_by": "human",
            "resolved_at": now,
        }
        if body.notes is not None:
            update["notes"] = body.notes

        response = (
            supabase.table("validation_council_decisions")
            .update(update)
            .eq("id", decision_id)
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=404, detail=f"Decision {decision_id} not found")

        return {"ok": True, "decision_id": decision_id, "resolved_at": now}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting decision {decision_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to reject decision: {str(e)}")


@router.get("/decisions")
async def list_decisions(
    limit: int = Query(50, ge=1, le=500),
    decision: str | None = Query(None, description="Filter by decision type"),
):
    """List all council decisions, optionally filtered by decision type."""
    try:
        supabase = get_supabase_client()
        query = supabase.table("validation_council_decisions").select("*")
        if decision:
            query = query.eq("decision", decision)
        response = query.order("created_at", desc=True).limit(limit).execute()
        entries = response.data or []
        return {"entries": entries, "count": len(entries)}
    except Exception as e:
        logger.error(f"Error listing decisions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list decisions: {str(e)}")
