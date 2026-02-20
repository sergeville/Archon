"""
API routes for the Unified Audit Log.

Provides a shared timeline for all Archon subsystems to log and query
audit events (Alfred, Situation Agent, Validation Council, Work Orders).
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)
router = APIRouter(prefix="/api/audit", tags=["Audit Log"])


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class CreateAuditEntryRequest(BaseModel):
    source: str = Field(..., description="System that generated the event")
    action: str = Field(..., description="What happened")
    agent: str | None = Field(None, description="Agent or user that triggered the event")
    target: str | None = Field(None, description="What was acted on")
    risk_level: str = Field("LOW", description="LOW | MED | HIGH | DESTRUCTIVE")
    outcome: str | None = Field(None, description="success | failed | blocked | approved")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary extra data")
    session_id: str | None = Field(None, description="Optional Archon session UUID")


class AuditEntryResponse(BaseModel):
    id: str
    timestamp: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("", response_model=AuditEntryResponse)
async def create_audit_entry(request: CreateAuditEntryRequest):
    """Insert one audit-log entry."""
    try:
        supabase = get_supabase_client()
        row: dict[str, Any] = {
            "source": request.source,
            "action": request.action,
            "risk_level": request.risk_level,
            "metadata": request.metadata,
        }
        if request.agent is not None:
            row["agent"] = request.agent
        if request.target is not None:
            row["target"] = request.target
        if request.outcome is not None:
            row["outcome"] = request.outcome
        if request.session_id is not None:
            row["session_id"] = request.session_id

        response = supabase.table("unified_audit_log").insert(row).execute()
        if not response.data:
            raise Exception("Insert returned no data")

        entry = response.data[0]
        return AuditEntryResponse(id=entry["id"], timestamp=entry["timestamp"])
    except Exception as e:
        logger.error(f"Error creating audit entry: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create audit entry: {str(e)}")


@router.get("")
async def list_audit_entries(
    source: str | None = Query(None, description="Filter by source"),
    risk_level: str | None = Query(None, description="Filter by risk level"),
    limit: int = Query(50, ge=1, le=500, description="Max entries to return"),
):
    """List audit-log entries ordered by timestamp DESC."""
    try:
        supabase = get_supabase_client()
        query = supabase.table("unified_audit_log").select("*")
        if source:
            query = query.eq("source", source)
        if risk_level:
            query = query.eq("risk_level", risk_level)
        response = query.order("timestamp", desc=True).limit(limit).execute()
        return {"entries": response.data or [], "count": len(response.data or [])}
    except Exception as e:
        logger.error(f"Error listing audit entries: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list audit entries: {str(e)}")
