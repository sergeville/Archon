"""
Session Service for Archon Short-Term Memory.

Handles CRUD operations for agent sessions and session events.
Provides temporal queries, semantic search, and session summarization.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from ..config.database import get_supabase_client
from ..config.logfire_config import get_logger
from ..utils.embeddings import get_embedding_service

logger = get_logger(__name__)


class SessionService:
    """
    Service for managing agent work sessions.

    Sessions represent continuous work periods by agents (claude, gemini, gpt, user).
    Each session can contain multiple events and be linked to a project.

    Short-term memory layer: Bridges working memory (current tasks) and
    long-term memory (knowledge base) by tracking recent activity.
    """

    def __init__(self):
        """Initialize the session service with database and embedding clients."""
        self.supabase = get_supabase_client()
        self.embedding_service = get_embedding_service()

    async def create_session(
        self,
        agent: str,
        project_id: Optional[UUID] = None,
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Create a new agent session.

        Args:
            agent: Agent identifier (claude, gemini, gpt, user)
            project_id: Optional UUID of associated project
            metadata: Optional additional context

        Returns:
            Created session dictionary

        Example:
            session = await service.create_session(
                agent="claude",
                project_id="uuid-here",
                metadata={"context": "Phase 2 implementation"}
            )
        """
        try:
            logger.info(f"Creating new session for agent: {agent}")

            # Prepare session data
            session_data = {
                "agent": agent,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata or {}
            }

            if project_id:
                session_data["project_id"] = str(project_id)

            # Insert session
            response = self.supabase.table("archon_sessions").insert(
                session_data
            ).execute()

            if not response.data:
                raise Exception("Session creation returned no data")

            session = response.data[0]

            logger.info(
                f"Session created: {session['id']} for {agent} "
                f"(project: {project_id or 'none'})"
            )

            return session

        except Exception as e:
            logger.error(f"Failed to create session: {e}", exc_info=True)
            raise

    async def end_session(
        self,
        session_id: UUID,
        summary: Optional[str] = None
    ) -> dict:
        """
        End a session and optionally add a summary.

        Args:
            session_id: UUID of session to end
            summary: Optional summary text (can be AI-generated later)

        Returns:
            Updated session dictionary

        Example:
            ended = await service.end_session(
                session_id=uuid,
                summary="Completed Phase 2 Day 1 database migration"
            )
        """
        try:
            logger.info(f"Ending session: {session_id}")

            # Prepare update data
            update_data = {
                "ended_at": datetime.now(timezone.utc).isoformat()
            }

            if summary:
                update_data["summary"] = summary

                # Generate embedding for summary if provided
                embedding = await self.embedding_service.generate_embedding(summary)
                if embedding:
                    update_data["embedding"] = embedding

            # Update session
            response = self.supabase.table("archon_sessions").update(
                update_data
            ).eq("id", str(session_id)).execute()

            if not response.data:
                raise Exception(f"Session not found: {session_id}")

            session = response.data[0]

            logger.info(f"Session ended: {session_id}")

            return session

        except Exception as e:
            logger.error(f"Failed to end session: {e}", exc_info=True)
            raise

    async def add_event(
        self,
        session_id: UUID,
        event_type: str,
        event_data: dict
    ) -> dict:
        """
        Log an event to a session.

        Event types:
        - task_created: Agent created a task
        - task_updated: Agent updated a task
        - task_completed: Agent completed a task
        - decision_made: Agent made a decision
        - error_encountered: Error occurred
        - pattern_identified: Pattern recognized
        - context_shared: Context shared with another agent

        Args:
            session_id: UUID of parent session
            event_type: Type of event (see above)
            event_data: Event-specific data (JSON)

        Returns:
            Created event dictionary

        Example:
            event = await service.add_event(
                session_id=uuid,
                event_type="task_created",
                event_data={"task_id": "123", "title": "New task"}
            )
        """
        try:
            logger.debug(f"Adding event to session {session_id}: {event_type}")

            # Prepare event data
            event_record = {
                "session_id": str(session_id),
                "event_type": event_type,
                "event_data": event_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Generate embedding for event
            embedding = await self.embedding_service.generate_event_embedding({
                "event_type": event_type,
                "event_data": event_data
            })
            if embedding:
                event_record["embedding"] = embedding

            # Insert event
            response = self.supabase.table("archon_session_events").insert(
                event_record
            ).execute()

            if not response.data:
                raise Exception("Event creation returned no data")

            event = response.data[0]

            logger.info(
                f"Event logged: {event_type} for session {session_id}"
            )

            return event

        except Exception as e:
            logger.error(f"Failed to add event: {e}", exc_info=True)
            raise

    async def get_session(self, session_id: UUID) -> Optional[dict]:
        """
        Get a session with its events.

        Args:
            session_id: UUID of session to retrieve

        Returns:
            Session dictionary with events, or None if not found

        Example:
            session = await service.get_session(uuid)
            print(f"Session summary: {session['summary']}")
            print(f"Event count: {len(session['events'])}")
        """
        try:
            # Get session
            response = self.supabase.table("archon_sessions").select(
                "*"
            ).eq("id", str(session_id)).execute()

            if not response.data:
                logger.warning(f"Session not found: {session_id}")
                return None

            session = response.data[0]

            # Get events for this session
            events_response = self.supabase.table("archon_session_events").select(
                "*"
            ).eq("session_id", str(session_id)).order(
                "timestamp", desc=False
            ).execute()

            session["events"] = events_response.data or []

            logger.debug(
                f"Retrieved session {session_id} with {len(session['events'])} events"
            )

            return session

        except Exception as e:
            logger.error(f"Failed to get session: {e}", exc_info=True)
            raise

    async def list_sessions(
        self,
        agent: Optional[str] = None,
        project_id: Optional[UUID] = None,
        since: Optional[datetime] = None,
        limit: int = 20
    ) -> list[dict]:
        """
        List recent sessions with optional filters.

        Args:
            agent: Filter by agent name
            project_id: Filter by project UUID
            since: Filter sessions started after this datetime
            limit: Maximum number of sessions to return (default: 20)

        Returns:
            List of session dictionaries

        Example:
            # Get last 10 sessions for claude
            sessions = await service.list_sessions(
                agent="claude",
                limit=10
            )

            # Get sessions from last 7 days
            week_ago = datetime.now(timezone.utc) - timedelta(days=7)
            sessions = await service.list_sessions(since=week_ago)
        """
        try:
            # Build query
            query = self.supabase.table("archon_sessions").select("*")

            if agent:
                query = query.eq("agent", agent)

            if project_id:
                query = query.eq("project_id", str(project_id))

            if since:
                query = query.gte("started_at", since.isoformat())

            # Execute with ordering and limit
            response = query.order("started_at", desc=True).limit(limit).execute()

            sessions = response.data or []

            logger.info(
                f"Listed {len(sessions)} sessions "
                f"(agent: {agent or 'all'}, limit: {limit})"
            )

            return sessions

        except Exception as e:
            logger.error(f"Failed to list sessions: {e}", exc_info=True)
            raise

    async def search_sessions(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.7
    ) -> list[dict]:
        """
        Search sessions using semantic similarity.

        Args:
            query: Search query text
            limit: Maximum results to return
            threshold: Minimum similarity score (0-1, default 0.7)

        Returns:
            List of matching sessions with similarity scores

        Example:
            results = await service.search_sessions(
                query="database migration errors",
                limit=5,
                threshold=0.75
            )
            for result in results:
                print(f"{result['similarity']:.2f}: {result['summary']}")
        """
        try:
            logger.info(f"Searching sessions for: {query[:50]}...")

            # Generate embedding for query
            query_embedding = await self.embedding_service.generate_embedding(query)

            if not query_embedding:
                logger.warning("Failed to generate query embedding")
                return []

            # Call database function for semantic search
            response = self.supabase.rpc(
                "search_sessions_semantic",
                {
                    "p_query_embedding": query_embedding,
                    "p_limit": limit,
                    "p_threshold": threshold
                }
            ).execute()

            results = response.data or []

            logger.info(
                f"Search returned {len(results)} sessions "
                f"(threshold: {threshold})"
            )

            return results

        except Exception as e:
            logger.error(f"Failed to search sessions: {e}", exc_info=True)
            raise

    async def get_last_session(self, agent: str) -> Optional[dict]:
        """
        Get the most recent session for an agent.

        Useful for resuming context from previous work.

        Args:
            agent: Agent identifier

        Returns:
            Most recent session dictionary, or None if no sessions exist

        Example:
            last = await service.get_last_session("claude")
            if last:
                print(f"Last session: {last['summary']}")
                print(f"Ended: {last['ended_at']}")
        """
        try:
            # Use database function
            response = self.supabase.rpc(
                "get_last_session",
                {"p_agent": agent}
            ).execute()

            if not response.data:
                logger.info(f"No previous sessions found for {agent}")
                return None

            session = response.data[0]

            # Get events for this session
            events_response = self.supabase.table("archon_session_events").select(
                "*"
            ).eq("session_id", session["id"]).order(
                "timestamp", desc=False
            ).execute()

            session["events"] = events_response.data or []

            logger.info(
                f"Retrieved last session for {agent}: {session['id']} "
                f"({len(session['events'])} events)"
            )

            return session

        except Exception as e:
            logger.error(f"Failed to get last session: {e}", exc_info=True)
            raise

    async def count_sessions(
        self,
        agent: str,
        days: int = 30
    ) -> int:
        """
        Count sessions for an agent in the last N days.

        Args:
            agent: Agent identifier
            days: Number of days to look back (default: 30)

        Returns:
            Number of sessions

        Example:
            count = await service.count_sessions("claude", days=7)
            print(f"Sessions this week: {count}")
        """
        try:
            # Use database function
            response = self.supabase.rpc(
                "count_sessions_by_agent",
                {
                    "p_agent": agent,
                    "p_days": days
                }
            ).execute()

            count = response.data if response.data is not None else 0

            logger.debug(f"{agent} has {count} sessions in last {days} days")

            return count

        except Exception as e:
            logger.error(f"Failed to count sessions: {e}", exc_info=True)
            raise

    async def get_recent_sessions(
        self,
        agent: str,
        days: int = 7,
        limit: int = 20
    ) -> list[dict]:
        """
        Get recent sessions for an agent using database function.

        More efficient than list_sessions for this specific query.

        Args:
            agent: Agent identifier
            days: Number of days to look back (default: 7)
            limit: Maximum sessions to return (default: 20)

        Returns:
            List of recent sessions with event counts

        Example:
            recent = await service.get_recent_sessions("claude", days=7)
            for session in recent:
                print(f"{session['started_at']}: {session['event_count']} events")
        """
        try:
            # Use database function
            response = self.supabase.rpc(
                "get_recent_sessions",
                {
                    "p_agent": agent,
                    "p_days": days,
                    "p_limit": limit
                }
            ).execute()

            sessions = response.data or []

            logger.info(
                f"Retrieved {len(sessions)} recent sessions for {agent} "
                f"(last {days} days)"
            )

            return sessions

        except Exception as e:
            logger.error(f"Failed to get recent sessions: {e}", exc_info=True)
            raise

    async def update_session_summary(
        self,
        session_id: UUID,
        summary: str,
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Update a session's summary and metadata.

        Used after AI summarization generates the summary.

        Args:
            session_id: UUID of session to update
            summary: Summary text
            metadata: Optional metadata (key_events, decisions, outcomes, next_steps)

        Returns:
            Updated session dictionary

        Example:
            updated = await service.update_session_summary(
                session_id=uuid,
                summary="Completed database migration...",
                metadata={
                    "key_events": ["tables_created", "indexes_added"],
                    "decisions": ["use pgvector"],
                    "outcomes": ["database ready"],
                    "next_steps": ["implement SessionService"]
                }
            )
        """
        try:
            logger.info(f"Updating summary for session {session_id}")

            # Generate embedding for summary
            embedding = await self.embedding_service.generate_embedding(summary)

            # Prepare update
            update_data = {"summary": summary}

            if embedding:
                update_data["embedding"] = embedding

            if metadata:
                update_data["metadata"] = metadata

            # Update session
            response = self.supabase.table("archon_sessions").update(
                update_data
            ).eq("id", str(session_id)).execute()

            if not response.data:
                raise Exception(f"Session not found: {session_id}")

            session = response.data[0]

            logger.info(f"Summary updated for session {session_id}")

            return session

        except Exception as e:
            logger.error(f"Failed to update session summary: {e}", exc_info=True)
            raise

    async def get_active_sessions(self) -> list[dict]:
        """
        Get all currently active (not ended) sessions.

        Returns:
            List of active session dictionaries

        Example:
            active = await service.get_active_sessions()
            print(f"Currently active: {len(active)} sessions")
        """
        try:
            response = self.supabase.table("archon_sessions").select(
                "*"
            ).is_("ended_at", "null").order("started_at", desc=True).execute()

            sessions = response.data or []

            logger.info(f"Retrieved {len(sessions)} active sessions")

            return sessions

        except Exception as e:
            logger.error(f"Failed to get active sessions: {e}", exc_info=True)
            raise


# Singleton instance for convenience
_session_service: Optional[SessionService] = None


def get_session_service() -> SessionService:
    """
    Get or create the singleton SessionService instance.

    Returns:
        Shared SessionService instance

    Example:
        service = get_session_service()
        session = await service.create_session("claude")
    """
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service
