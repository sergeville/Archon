"""
Session Handoff Service for Archon Shared Memory.

Manages the lifecycle of work handoffs between agents: creating a pending
handoff, accepting it, completing or rejecting it, and querying by agent
or session.
"""
from datetime import UTC, datetime

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)


class HandoffService:
    """Service for managing session handoffs between agents."""

    def __init__(self):
        """Initialize the handoff service."""
        self.supabase = get_supabase_client()

    async def create_handoff(
        self,
        session_id: str,
        from_agent: str,
        to_agent: str,
        context: dict | None = None,
        notes: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """
        Create a new pending handoff.

        Args:
            session_id: UUID of the session being handed off
            from_agent: Agent initiating the handoff
            to_agent: Agent that should receive the work
            context: Structured context payload (task state, progress, etc.)
            notes: Free-text instructions for the receiving agent
            metadata: Additional metadata

        Returns:
            Created handoff record
        """
        try:
            logger.info(f"Creating handoff from {from_agent} to {to_agent} for session {session_id}")
            handoff_data = {
                "session_id": session_id,
                "from_agent": from_agent,
                "to_agent": to_agent,
                "context": context or {},
                "notes": notes,
                "status": "pending",
                "metadata": metadata or {},
            }
            response = (
                self.supabase.table("archon_session_handoffs")
                .insert(handoff_data)
                .execute()
            )
            if not response.data:
                raise Exception("Handoff creation returned no data")
            handoff = response.data[0]
            logger.info(f"Handoff created: {handoff['id']}")
            return handoff
        except Exception as e:
            logger.error(f"Failed to create handoff: {e}", exc_info=True)
            raise

    async def accept_handoff(self, handoff_id: str) -> dict:
        """
        Accept a pending handoff.

        Sets accepted_at timestamp and transitions status to "accepted".

        Args:
            handoff_id: UUID of the handoff

        Returns:
            Updated handoff record
        """
        try:
            response = (
                self.supabase.table("archon_session_handoffs")
                .update({
                    "status": "accepted",
                    "accepted_at": datetime.now(UTC).isoformat(),
                })
                .eq("id", handoff_id)
                .execute()
            )
            if not response.data:
                raise Exception(f"Handoff '{handoff_id}' not found for acceptance")
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to accept handoff {handoff_id}: {e}", exc_info=True)
            raise

    async def complete_handoff(self, handoff_id: str) -> dict:
        """
        Complete an accepted handoff.

        Sets completed_at timestamp and transitions status to "completed".

        Args:
            handoff_id: UUID of the handoff

        Returns:
            Updated handoff record
        """
        try:
            response = (
                self.supabase.table("archon_session_handoffs")
                .update({
                    "status": "completed",
                    "completed_at": datetime.now(UTC).isoformat(),
                })
                .eq("id", handoff_id)
                .execute()
            )
            if not response.data:
                raise Exception(f"Handoff '{handoff_id}' not found for completion")
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to complete handoff {handoff_id}: {e}", exc_info=True)
            raise

    async def reject_handoff(self, handoff_id: str) -> dict:
        """
        Reject a pending handoff.

        Transitions status to "rejected".

        Args:
            handoff_id: UUID of the handoff

        Returns:
            Updated handoff record
        """
        try:
            response = (
                self.supabase.table("archon_session_handoffs")
                .update({"status": "rejected"})
                .eq("id", handoff_id)
                .execute()
            )
            if not response.data:
                raise Exception(f"Handoff '{handoff_id}' not found for rejection")
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to reject handoff {handoff_id}: {e}", exc_info=True)
            raise

    async def get_pending_handoffs(self, agent: str) -> list[dict]:
        """
        Get all pending handoffs addressed to a specific agent.

        Args:
            agent: Agent name to query for

        Returns:
            List of pending handoff records ordered by created_at ascending
        """
        try:
            response = (
                self.supabase.table("archon_session_handoffs")
                .select("*")
                .eq("to_agent", agent)
                .eq("status", "pending")
                .order("created_at", desc=False)
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error(f"Failed to get pending handoffs for agent {agent}: {e}", exc_info=True)
            raise

    async def get_handoff(self, handoff_id: str) -> dict | None:
        """
        Get a handoff by ID.

        Args:
            handoff_id: UUID of the handoff

        Returns:
            Handoff record or None if not found
        """
        try:
            response = (
                self.supabase.table("archon_session_handoffs")
                .select("*")
                .eq("id", handoff_id)
                .execute()
            )
            if not response.data:
                return None
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to get handoff {handoff_id}: {e}", exc_info=True)
            raise

    async def list_handoffs(
        self,
        session_id: str | None = None,
        agent: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        """
        List handoffs with optional filters.

        Args:
            session_id: Filter by session UUID
            agent: Filter by to_agent name
            status: Filter by status (pending, accepted, completed, rejected)

        Returns:
            List of handoff records ordered by created_at descending
        """
        try:
            query = self.supabase.table("archon_session_handoffs").select("*")
            if session_id:
                query = query.eq("session_id", session_id)
            if agent:
                query = query.eq("to_agent", agent)
            if status:
                query = query.eq("status", status)
            response = query.order("created_at", desc=True).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Failed to list handoffs: {e}", exc_info=True)
            raise


# Singleton instance
_handoff_service: HandoffService | None = None


def get_handoff_service() -> HandoffService:
    """Get or create the singleton HandoffService instance."""
    global _handoff_service
    if _handoff_service is None:
        _handoff_service = HandoffService()
    return _handoff_service
