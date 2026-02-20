"""
HTTP 202 Accepted Response Protocol for Archon

Provides a standardized way to handle asynchronous requests that are 
accepted but not yet completed. This aligns with the PRD for autonomous
digital partners.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class AcceptedResponse(BaseModel):
    """Standardized response for HTTP 202 Accepted"""
    status: str = 'accepted'
    message: str = 'Request accepted and queued for processing'
    progress_id: str = Field(..., description='ID to track progress via polling')
    estimated_duration: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    follow_up_action: str = Field(..., description='What the agent should do next (e.g., "poll_progress")')
    resource_type: str = Field(..., description='Type of resource being created/processed')
    polling_endpoint: Optional[str] = Field(None, description='URL to poll for completion status')

def create_202_response(
    progress_id: str, 
    follow_up_action: str, 
    resource_type: str, 
    message: str = None,
    polling_endpoint: str = None
) -> dict[str, Any]:
    """Helper to create a standardized 202 response body"""
    response = AcceptedResponse(
        progress_id=progress_id,
        follow_up_action=follow_up_action,
        resource_type=resource_type,
        polling_endpoint=polling_endpoint
    )
    if message:
        response.message = message
    return response.model_dump()

class FollowUpPlan(BaseModel):
    """Model representing an agent's plan to follow up on a 202 response"""
    action: str = 'monitor_completion'
    progress_id: str
    resource_type: str
    target_status: str = 'completed'
    max_attempts: int = 30
    polling_interval: float = 2.0
    intervention_logic: str = Field(..., description='Description of when the agent should intervene')

def generate_follow_up_plan(accepted_data: dict[str, Any]) -> FollowUpPlan:
    """Generate a structured plan for the agent based on a 202 response"""
    return FollowUpPlan(
        progress_id=accepted_data.get('progress_id', 'unknown'),
        resource_type=accepted_data.get('resource_type', 'unknown'),
        intervention_logic='If status remains "failed" or "stuck" for > 5 mins, escalate to user.'
    )
