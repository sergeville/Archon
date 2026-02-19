"""
Shared Context Service for Archon Shared Memory.

Provides a cross-agent key/value board that agents use to broadcast and
consume shared state (e.g. current project, active task, environment flags).
All writes are audited to archon_shared_context_history via a DB trigger.
"""
from typing import Any

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)


class SharedContextService:
    """Service for managing the shared context board."""

    def __init__(self):
        """Initialize the shared context service."""
        self.supabase = get_supabase_client()

    async def set_context(
        self,
        key: str,
        value: Any,
        set_by: str,
        session_id: str | None = None,
        expires_at: str | None = None,
    ) -> dict:
        """
        Set or update a context entry by key (upsert).

        Args:
            key: Unique context key
            value: JSON-serialisable value
            set_by: Agent or user that is writing the value
            session_id: Optional session UUID to link this context entry to
            expires_at: Optional ISO-8601 expiry timestamp

        Returns:
            Upserted context record
        """
        try:
            logger.info(f"Setting context key '{key}' by {set_by}")
            context_data: dict = {
                "context_key": key,
                "value": value,
                "set_by": set_by,
            }
            if session_id:
                context_data["session_id"] = session_id
            if expires_at:
                context_data["expires_at"] = expires_at

            response = (
                self.supabase.table("archon_shared_context")
                .upsert(context_data, on_conflict="context_key")
                .execute()
            )
            if not response.data:
                raise Exception("Set context returned no data")
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to set context key '{key}': {e}", exc_info=True)
            raise

    async def get_context(self, key: str) -> dict | None:
        """
        Get a context entry by key.

        Args:
            key: Context key

        Returns:
            Context record or None if not found
        """
        try:
            response = (
                self.supabase.table("archon_shared_context")
                .select("*")
                .eq("context_key", key)
                .execute()
            )
            if not response.data:
                return None
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to get context key '{key}': {e}", exc_info=True)
            raise

    async def list_context(self, prefix: str | None = None) -> list[dict]:
        """
        List all context entries, optionally filtered by key prefix.

        Args:
            prefix: Optional key prefix filter (e.g. "project/" returns
                    all keys that start with "project/")

        Returns:
            List of context records ordered by updated_at descending
        """
        try:
            query = self.supabase.table("archon_shared_context").select("*")
            if prefix:
                query = query.like("context_key", f"{prefix}%")
            response = query.order("updated_at", desc=True).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Failed to list context: {e}", exc_info=True)
            raise

    async def delete_context(self, key: str) -> bool:
        """
        Delete a context entry by key.

        Args:
            key: Context key to delete

        Returns:
            True if deleted, False if key not found
        """
        try:
            response = (
                self.supabase.table("archon_shared_context")
                .delete()
                .eq("context_key", key)
                .execute()
            )
            deleted = bool(response.data)
            logger.info(f"Context key '{key}' {'deleted' if deleted else 'not found'}")
            return deleted
        except Exception as e:
            logger.error(f"Failed to delete context key '{key}': {e}", exc_info=True)
            raise

    async def get_history(self, key: str, limit: int = 20) -> list[dict]:
        """
        Get the change history for a context key.

        Args:
            key: Context key
            limit: Maximum number of history records to return

        Returns:
            List of history records ordered by changed_at descending
        """
        try:
            response = (
                self.supabase.table("archon_shared_context_history")
                .select("*")
                .eq("context_key", key)
                .order("changed_at", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error(f"Failed to get history for context key '{key}': {e}", exc_info=True)
            raise


# Singleton instance
_shared_context_service: SharedContextService | None = None


def get_shared_context_service() -> SharedContextService:
    """Get or create the singleton SharedContextService instance."""
    global _shared_context_service
    if _shared_context_service is None:
        _shared_context_service = SharedContextService()
    return _shared_context_service
