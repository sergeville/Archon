"""
Memory Service for Archon Conversation History.

Handles conversation message storage, retrieval, and semantic search.
Works in conjunction with SessionService for complete memory management.
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from ..utils import get_supabase_client
from ..config.logfire_config import get_logger
from ..utils.embeddings import get_embedding_service
from .session_service import SessionService

logger = get_logger(__name__)


class MemoryService:
    """
    Service for managing conversation history and memory operations.

    Handles conversation messages (user/assistant/system) within sessions,
    providing storage, retrieval, and semantic search capabilities.

    Conversation messages represent the actual dialogue between users and AI,
    while sessions (managed by SessionService) represent work periods.
    """

    def __init__(self):
        """Initialize the memory service with database and embedding clients."""
        self.supabase = get_supabase_client()
        self.embedding_service = get_embedding_service()
        self.session_service = SessionService()

    async def create_session(
        self,
        agent: str,
        project_id: Optional[UUID] = None,
        context: Optional[dict] = None,
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Create a new agent session.

        Delegates to SessionService for session creation.
        Provided here for convenience and backward compatibility.

        Args:
            agent: Agent identifier (claude, gemini, gpt, user)
            project_id: Optional UUID of associated project
            context: Optional session context data
            metadata: Optional additional metadata

        Returns:
            Created session dictionary with id, agent, started_at, etc.

        Raises:
            Exception: If session creation fails

        Example:
            session = await memory_service.create_session(
                agent="claude",
                project_id=uuid.UUID("..."),
                context={"working_on": "Phase 2"},
                metadata={"environment": "production"}
            )
        """
        return await self.session_service.create_session(
            agent=agent,
            project_id=project_id,
            context=context,
            metadata=metadata
        )

    async def end_session(
        self,
        session_id: UUID,
        summary: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> dict:
        """
        End an active session.

        Delegates to SessionService for session completion.
        Optionally generates AI summary if not provided.

        Args:
            session_id: UUID of the session to end
            summary: Optional session summary text
            metadata: Optional additional metadata

        Returns:
            Updated session dictionary with ended_at timestamp

        Raises:
            Exception: If session not found or update fails

        Example:
            ended = await memory_service.end_session(
                session_id=uuid.UUID("..."),
                summary="Completed Phase 2 migration tasks"
            )
        """
        return await self.session_service.end_session(
            session_id=session_id,
            summary=summary,
            metadata=metadata
        )

    async def store_message(
        self,
        session_id: UUID,
        role: str,
        message: str,
        tools_used: Optional[list[str]] = None,
        message_type: Optional[str] = None,
        subtype: Optional[str] = None,
        metadata: Optional[dict] = None,
        generate_embedding: bool = True
    ) -> dict:
        """
        Store a conversation message in the database.

        Args:
            session_id: UUID of the session this message belongs to
            role: Message role - must be 'user', 'assistant', or 'system'
            message: The message content text
            tools_used: Optional list of tools used (for assistant messages)
            message_type: Optional MeshOS taxonomy type (e.g., 'command', 'question')
            subtype: Optional MeshOS taxonomy subtype (e.g., 'clarification')
            metadata: Optional additional metadata as dict
            generate_embedding: Whether to generate vector embedding (default True)

        Returns:
            Created conversation message dictionary

        Raises:
            ValueError: If role is not valid or session_id doesn't exist
            Exception: If database insert fails

        Example:
            # User message
            user_msg = await memory_service.store_message(
                session_id=uuid.UUID("..."),
                role="user",
                message="Create a database migration",
                message_type="command",
                subtype="task_request"
            )

            # Assistant message with tools
            assistant_msg = await memory_service.store_message(
                session_id=uuid.UUID("..."),
                role="assistant",
                message="I'll create the migration file.",
                tools_used=["database", "migration"],
                message_type="response",
                subtype="acknowledgment"
            )
        """
        try:
            # Validate role
            valid_roles = ["user", "assistant", "system"]
            if role not in valid_roles:
                raise ValueError(
                    f"Invalid role '{role}'. Must be one of: {', '.join(valid_roles)}"
                )

            logger.info(
                f"Storing {role} message in session {session_id} "
                f"(length: {len(message)} chars)"
            )

            # Prepare message data
            message_data = {
                "session_id": str(session_id),
                "role": role,
                "message": message,
                "tools_used": tools_used or [],
                "type": message_type,
                "subtype": subtype,
                "metadata": metadata or {},
                "created_at": datetime.now(timezone.utc).isoformat()
            }

            # Generate embedding if requested
            if generate_embedding:
                try:
                    # Create embedding-optimized text
                    embedding_text = f"{role}: {message}"
                    if message_type:
                        embedding_text = f"[{message_type}] {embedding_text}"

                    embedding = await self.embedding_service.generate_embedding(
                        embedding_text
                    )
                    message_data["embedding"] = embedding
                    logger.debug(f"Generated embedding for message (dim: {len(embedding)})")
                except Exception as e:
                    logger.warning(
                        f"Failed to generate embedding for message: {e}. "
                        "Storing without embedding."
                    )

            # Insert into database
            response = self.supabase.table("conversation_history").insert(
                message_data
            ).execute()

            if not response.data:
                raise Exception("Message storage returned no data")

            stored_message = response.data[0]

            logger.info(
                f"Message stored: {stored_message['id']} "
                f"(role: {role}, type: {message_type or 'none'})"
            )

            return stored_message

        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            logger.error(
                f"Failed to store message in session {session_id}: {e}",
                exc_info=True
            )
            raise

    async def get_session_history(
        self,
        session_id: UUID,
        limit: int = 100,
        role_filter: Optional[str] = None,
        include_embeddings: bool = False
    ) -> list[dict]:
        """
        Retrieve conversation history for a session.

        Returns messages in chronological order (oldest first).

        Args:
            session_id: UUID of the session
            limit: Maximum number of messages to return (default 100)
            role_filter: Optional filter by role ('user', 'assistant', 'system')
            include_embeddings: Whether to include embedding vectors (default False)

        Returns:
            List of conversation message dictionaries, ordered by created_at ASC

        Raises:
            Exception: If database query fails

        Example:
            # Get all messages
            history = await memory_service.get_session_history(
                session_id=uuid.UUID("...")
            )

            # Get only user messages
            user_messages = await memory_service.get_session_history(
                session_id=uuid.UUID("..."),
                role_filter="user"
            )

            # Get recent 10 messages
            recent = await memory_service.get_session_history(
                session_id=uuid.UUID("..."),
                limit=10
            )
        """
        try:
            logger.info(
                f"Retrieving conversation history for session {session_id} "
                f"(limit: {limit}, role: {role_filter or 'all'})"
            )

            # Build query
            query = self.supabase.table("conversation_history").select(
                "*" if include_embeddings else "id,session_id,role,message,tools_used,type,subtype,created_at,metadata"
            ).eq("session_id", str(session_id))

            # Apply role filter if specified
            if role_filter:
                query = query.eq("role", role_filter)

            # Order by created_at ascending and apply limit
            query = query.order("created_at", desc=False).limit(limit)

            # Execute query
            response = query.execute()

            messages = response.data or []

            logger.info(
                f"Retrieved {len(messages)} messages for session {session_id}"
            )

            return messages

        except Exception as e:
            logger.error(
                f"Failed to retrieve conversation history for {session_id}: {e}",
                exc_info=True
            )
            raise

    async def search_conversations(
        self,
        query: str,
        session_id: Optional[UUID] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        role_filter: Optional[str] = None
    ) -> list[dict]:
        """
        Search conversation messages using semantic similarity.

        Uses vector embeddings to find messages similar to the query text.
        Can search across all sessions or within a specific session.

        Args:
            query: Search query text
            session_id: Optional UUID to search within specific session only
            limit: Maximum number of results (default 10)
            similarity_threshold: Minimum similarity score 0-1 (default 0.7)
            role_filter: Optional filter by role ('user', 'assistant', 'system')

        Returns:
            List of matching messages with similarity scores, ordered by relevance

        Raises:
            Exception: If embedding generation or search fails

        Example:
            # Search all conversations
            results = await memory_service.search_conversations(
                query="database migration issues",
                limit=5
            )

            # Search within specific session
            results = await memory_service.search_conversations(
                query="authentication problems",
                session_id=uuid.UUID("..."),
                limit=10
            )

            # Search only user messages
            user_results = await memory_service.search_conversations(
                query="error messages",
                role_filter="user"
            )
        """
        try:
            logger.info(
                f"Searching conversations for: '{query[:50]}...' "
                f"(session: {session_id or 'all'}, threshold: {similarity_threshold})"
            )

            # Generate embedding for query
            query_embedding = await self.embedding_service.generate_embedding(query)

            logger.debug(f"Generated query embedding (dim: {len(query_embedding)})")

            # Use database function for semantic search
            rpc_params = {
                "p_query_embedding": query_embedding,
                "p_match_count": limit,
                "p_threshold": similarity_threshold
            }

            # Add session filter if specified
            if session_id:
                rpc_params["p_session_id"] = str(session_id)

            # Call search_conversation_semantic function
            response = self.supabase.rpc(
                "search_conversation_semantic",
                rpc_params
            ).execute()

            results = response.data or []

            # Apply role filter in Python if needed (function doesn't support it)
            if role_filter:
                results = [r for r in results if r.get("role") == role_filter]

            logger.info(
                f"Found {len(results)} matching conversations "
                f"(threshold: {similarity_threshold})"
            )

            return results

        except Exception as e:
            logger.error(f"Failed to search conversations: {e}", exc_info=True)
            raise


# Singleton instance
_memory_service_instance: Optional[MemoryService] = None


def get_memory_service() -> MemoryService:
    """
    Get the singleton memory service instance.

    Returns:
        MemoryService: The memory service instance

    Example:
        service = get_memory_service()
        session = await service.create_session(agent="claude")
    """
    global _memory_service_instance
    if _memory_service_instance is None:
        _memory_service_instance = MemoryService()
    return _memory_service_instance
