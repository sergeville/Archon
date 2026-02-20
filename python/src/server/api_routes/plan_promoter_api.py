"""
Plan Promoter API

Endpoints for listing plans from PLANS_INDEX.md and promoting
them to Archon projects with AI-generated tasks.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..config.logfire_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/plan-promoter", tags=["plan-promoter"])


class PromoteRequest(BaseModel):
    plan_path: str
    plan_name: str


@router.get("/plans")
async def list_plans():
    """List all plans from PLANS_INDEX.md with promotion status."""
    from ..services.plan_promoter_service import PlanPromoterService

    service = PlanPromoterService()
    try:
        plans = service.list_plans()
        return {"plans": plans, "count": len(plans)}
    except FileNotFoundError as e:
        return {"error": str(e), "plans": [], "count": 0}
    except Exception as e:
        logger.error(f"Error listing plans: {e}", exc_info=True)
        return {"error": str(e), "plans": [], "count": 0}


@router.post("/promote")
async def promote_plan(request: PromoteRequest):
    """Promote a plan to an Archon project with AI-generated tasks."""
    from ..services.plan_promoter_service import PlanPromoterService

    service = PlanPromoterService()
    success, result = await service.promote_plan(
        plan_path=request.plan_path,
        plan_name=request.plan_name,
    )

    if not success:
        raise HTTPException(status_code=400, detail=result)

    return result
