"""
Pattern Service for Archon Shared Memory.

Handles extraction, storage, and retrieval of behavioral and technical patterns.
Enables agents to learn from past experiences across the ecosystem.
"""
from datetime import datetime, timezone
from typing import Optional, List, Any
from uuid import UUID

from ..utils import get_supabase_client
from ..config.logfire_config import get_logger
from ..utils.embeddings import get_embedding_service

logger = get_logger(__name__)


class PatternService:
    """
    Service for managing patterns learned by agents.

    Patterns capture recurring sequences of actions, decisions, and outcomes.
    They represent the 'Wisdom' layer of the shared memory system.
    """

    def __init__(self):
        """Initialize the pattern service."""
        self.supabase = get_supabase_client()
        self.embedding_service = get_embedding_service()

    async def harvest_pattern(
        self,
        pattern_type: str,
        domain: str,
        description: str,
        action: str,
        outcome: Optional[str] = None,
        context: Optional[dict] = None,
        metadata: Optional[dict] = None,
        created_by: str = "system"
    ) -> dict:
        """
        Create and store a new learned pattern.

        Args:
            pattern_type: Type of pattern (success, failure, technical, process)
            domain: Application domain (development, management, hvac, etc.)
            description: Human-readable description of the pattern
            action: The action that constitutes the pattern
            outcome: Optional result of the action
            context: Environmental context data
            metadata: Additional metadata (confidence, etc.)
            created_by: Agent identifier

        Returns:
            Created pattern dictionary
        """
        try:
            logger.info(f"Harvesting new pattern in domain: {domain}")

            # Prepare pattern data
            pattern_data = {
                "pattern_type": pattern_type,
                "domain": domain,
                "description": description,
                "action": action,
                "outcome": outcome,
                "context": context or {},
                "metadata": metadata or {},
                "created_by": created_by,
                "created_at": datetime.now(timezone.utc).isoformat()
            }

            # Generate embedding for pattern (combining description and action)
            embedding_text = f"{description}. {action}. {outcome or ''}"
            embedding = await self.embedding_service.generate_embedding(embedding_text)
            if embedding:
                pattern_data["embedding"] = embedding

            # Insert pattern
            response = self.supabase.table("archon_patterns").insert(
                pattern_data
            ).execute()

            if not response.data:
                raise Exception("Pattern creation returned no data")

            pattern = response.data[0]
            logger.info(f"Pattern harvested: {pattern['id']} in {domain}")

            return pattern

        except Exception as e:
            logger.error(f"Failed to harvest pattern: {e}", exc_info=True)
            raise

    async def record_observation(
        self,
        pattern_id: UUID,
        session_id: Optional[UUID] = None,
        success_rating: Optional[int] = None,
        feedback: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Record an instance of a pattern being observed or applied.

        Args:
            pattern_id: UUID of the pattern
            session_id: UUID of the current session
            success_rating: Rating from 1-5
            feedback: Optional feedback text
            metadata: Additional metadata

        Returns:
            Created observation dictionary
        """
        try:
            observation_data = {
                "pattern_id": str(pattern_id),
                "observed_at": datetime.now(timezone.utc).isoformat(),
                "success_rating": success_rating,
                "feedback": feedback,
                "metadata": metadata or {}
            }

            if session_id:
                observation_data["session_id"] = str(session_id)

            response = self.supabase.table("archon_pattern_observations").insert(
                observation_data
            ).execute()

            if not response.data:
                raise Exception("Observation recording returned no data")

            observation = response.data[0]
            return observation

        except Exception as e:
            logger.error(f"Failed to record observation: {e}", exc_info=True)
            raise

    async def search_patterns(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.7,
        domain: Optional[str] = None
    ) -> List[dict]:
        """
        Search patterns using semantic similarity.

        Args:
            query: Search query text
            limit: Maximum results
            threshold: Minimum similarity score
            domain: Optional domain filter

        Returns:
            List of matching patterns
        """
        try:
            logger.info(f"Searching patterns for: {query[:50]}...")

            query_embedding = await self.embedding_service.generate_embedding(query)
            if not query_embedding:
                return []

            # Call database function
            # Note: domain filter would need to be added to the RPC or handled here
            response = self.supabase.rpc(
                "search_patterns_semantic",
                {
                    "p_query_embedding": query_embedding,
                    "p_limit": limit,
                    "p_threshold": threshold
                }
            ).execute()

            results = response.data or []

            if domain:
                results = [r for r in results if r.get('domain') == domain]

            logger.info(f"Search returned {len(results)} patterns")
            return results

        except Exception as e:
            logger.error(f"Failed to search patterns: {e}", exc_info=True)
            raise

    async def get_pattern(self, pattern_id: UUID) -> Optional[dict]:
        """Get a pattern by ID with its observation stats."""
        try:
            response = self.supabase.table("archon_patterns").select(
                "*"
            ).eq("id", str(pattern_id)).execute()

            if not response.data:
                return None

            pattern = response.data[0]

            # Get observation summary
            obs_response = self.supabase.table("archon_pattern_observations").select(
                "success_rating"
            ).eq("pattern_id", str(pattern_id)).execute()

            if obs_response.data:
                ratings = [r['success_rating'] for r in obs_response.data if r['success_rating']]
                pattern['observation_count'] = len(obs_response.data)
                pattern['average_rating'] = sum(ratings) / len(ratings) if ratings else None
            else:
                pattern['observation_count'] = 0
                pattern['average_rating'] = None

            return pattern

        except Exception as e:
            logger.error(f"Failed to get pattern: {e}", exc_info=True)
            raise

    async def extract_patterns_from_session(self, session_id: UUID) -> List[dict]:
        """
        Analyze session events and extract reusable patterns using AI.

        Calls PydanticAI to identify recurring sequences of actions, decisions,
        and outcomes, then stores each candidate via harvest_pattern().

        Args:
            session_id: UUID of the session to analyze

        Returns:
            List of created pattern dicts (empty if no patterns found or session missing)
        """
        from .session_service import get_session_service
        from ...agents.features.pattern_extractor import extract_patterns

        session_service = get_session_service()
        session = await session_service.get_session(session_id)

        if not session:
            logger.info(f"Session {session_id} not found — skipping extraction")
            return []

        events = session.get("events") or []
        logger.info(
            f"Extracting patterns from session {session_id} "
            f"({len(events)} events, agent: {session.get('agent', 'unknown')})"
        )

        extracted = await extract_patterns(session, events)
        logger.info(
            f"AI identified {len(extracted.patterns)} pattern candidates "
            f"— rationale: {extracted.rationale[:120]}"
        )

        created: List[dict] = []
        for candidate in extracted.patterns:
            if candidate.confidence < 0.6:
                logger.debug(
                    f"Skipping low-confidence pattern ({candidate.confidence:.2f}): "
                    f"{candidate.description[:60]}"
                )
                continue

            pattern = await self.harvest_pattern(
                pattern_type=candidate.pattern_type,
                domain=candidate.domain,
                description=candidate.description,
                action=candidate.action,
                outcome=candidate.outcome,
                context={"source_session_id": str(session_id)},
                metadata={"confidence": candidate.confidence, "extracted_by": "pattern_extractor"},
                created_by="pattern_extractor",
            )
            created.append(pattern)

        logger.info(f"Stored {len(created)} patterns from session {session_id}")
        return created

    async def list_patterns(
        self,
        pattern_type: Optional[str] = None,
        domain: Optional[str] = None,
        limit: int = 50
    ) -> List[dict]:
        """
        List patterns with optional filters.

        Args:
            pattern_type: Filter by type (success, failure, technical, process)
            domain: Filter by domain
            limit: Maximum results

        Returns:
            List of pattern dictionaries ordered by creation date descending
        """
        try:
            query = self.supabase.table("archon_patterns").select("*")

            if pattern_type:
                query = query.eq("pattern_type", pattern_type)
            if domain:
                query = query.eq("domain", domain)

            response = query.order("created_at", desc=True).limit(limit).execute()
            return response.data or []

        except Exception as e:
            logger.error(f"Failed to list patterns: {e}", exc_info=True)
            raise

    async def get_pattern_stats(self) -> dict:
        """Get global stats on learned patterns."""
        try:
            patterns_resp = self.supabase.table("archon_patterns").select("pattern_type", count="exact").execute()
            obs_resp = self.supabase.table("archon_pattern_observations").select("id", count="exact").execute()
            
            stats = {
                "total_patterns": patterns_resp.count,
                "total_observations": obs_resp.count,
                "by_type": {}
            }
            
            if patterns_resp.data:
                for p in patterns_resp.data:
                    ptype = p.get('pattern_type', 'unknown')
                    stats['by_type'][ptype] = stats['by_type'].get(ptype, 0) + 1
                    
            return stats
        except Exception as e:
            logger.error(f"Error getting pattern stats: {e}")
            return {"error": str(e)}


# Singleton instance
_pattern_service: Optional[PatternService] = None


def get_pattern_service() -> PatternService:
    """Get or create the singleton PatternService instance."""
    global _pattern_service
    if _pattern_service is None:
        _pattern_service = PatternService()
    return _pattern_service
