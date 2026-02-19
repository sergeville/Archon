# Phase 3 Day 1: Pattern Learning Database & Service Layer

**Status:** COMPLETE — all criteria met as of 2026-02-19
**Timeline:** 1 day (4-6 hours)
**Goal:** Create pattern storage and basic pattern service

---

## Prerequisites Check

### Required Before Starting
- [x] Phase 2 at 90%+ (core features working) ✅
- [ ] Migration 003 run (optional - semantic search)
- [ ] Anthropic API key configured (optional - AI features)
- [x] Docker services running ✅
- [x] Migration 004 file ready ✅

**Status:** Ready to proceed (optional items can be done anytime)

---

## Day 1 Objectives

1. **Run migration 004** - Create pattern tables in database
2. **Create PatternService** - Core business logic for patterns
3. **Write unit tests** - Test pattern CRUD operations
4. **Verify integration** - Test with actual database

---

## Step 1: Run Migration 004 (10 minutes)

### Migration File Location
```
migration/004_pattern_learning.sql
```

### What It Creates

**Tables:**
1. `archon_patterns` - Store identified patterns
   - pattern_type: success, failure, technical, process
   - domain: development, management, etc.
   - description, context, action, outcome
   - embedding (1536-dim vector for semantic search)
   - metadata (confidence scores, frequency, etc.)

2. `archon_pattern_observations` - Track pattern applications
   - Links to pattern_id and session_id
   - success_rating (1-5 scale)
   - feedback and metadata

**Functions:**
- `search_patterns_semantic()` - Find similar patterns by embedding

**Indexes:**
- Vector indexes for semantic search
- Type and domain indexes for filtering

### How to Run

#### Option A: Supabase Dashboard (Recommended)

```bash
# 1. Copy migration to clipboard
cat migration/004_pattern_learning.sql | pbcopy

# 2. Open Supabase
open "https://supabase.com/dashboard"

# 3. Go to SQL Editor → New Query
# 4. Paste and click "Run"
```

#### Option B: Verification Query

After running, verify with:
```sql
-- Check tables created
SELECT table_name
FROM information_schema.tables
WHERE table_name IN ('archon_patterns', 'archon_pattern_observations');

-- Should return 2 rows

-- Check function created
SELECT routine_name
FROM information_schema.routines
WHERE routine_name = 'search_patterns_semantic';

-- Should return 1 row
```

---

## Step 2: Create PatternService (2-3 hours)

### File to Create
```
python/src/server/services/pattern_service.py
```

### Implementation Outline

```python
"""
Pattern Learning Service for Archon

Manages pattern storage, retrieval, and recommendations.
Patterns represent proven approaches or known failure modes.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
from ..config.database import get_supabase_client
from ..utils.embeddings import EmbeddingService
from ..config.logfire_config import get_logger

logger = get_logger(__name__)

class PatternService:
    """
    Service for managing learned patterns.

    Patterns are identified behaviors or approaches that have been
    observed to produce consistent outcomes. They can be:
    - Technical patterns (database optimization, API design)
    - Process patterns (task breakdown, code review)
    - Success patterns (what worked well)
    - Failure patterns (what to avoid)
    """

    def __init__(self):
        self.supabase = get_supabase_client()
        self.embedding_service = EmbeddingService()

    async def create_pattern(
        self,
        pattern_type: str,
        domain: str,
        description: str,
        action: str,
        context: dict = None,
        outcome: str = None,
        created_by: str = "user",
        metadata: dict = None
    ) -> dict:
        """
        Create a new pattern.

        Args:
            pattern_type: success, failure, technical, process
            domain: development, management, specific area
            description: What the pattern is
            action: The action that constitutes the pattern
            context: Environmental conditions (optional)
            outcome: Result of applying the pattern (optional)
            created_by: Who identified this pattern
            metadata: Additional data (confidence, tags, etc.)

        Returns:
            Created pattern dictionary

        Example:
            pattern = await service.create_pattern(
                pattern_type="technical",
                domain="database",
                description="Query optimization via indexing",
                action="Add B-tree index on frequently queried columns",
                context={"technology": "PostgreSQL"},
                outcome="60-80% query time reduction",
                created_by="claude"
            )
        """
        try:
            # Generate embedding for semantic search
            embedding_text = f"{description} {action} {outcome or ''}"
            embedding = await self.embedding_service.generate_embedding(embedding_text)

            # Initialize metadata with defaults
            pattern_metadata = metadata or {}
            if "confidence_score" not in pattern_metadata:
                pattern_metadata["confidence_score"] = 0.5  # Initial confidence
            if "applications" not in pattern_metadata:
                pattern_metadata["applications"] = 0
            if "success_rate" not in pattern_metadata:
                pattern_metadata["success_rate"] = 0.0

            # Insert pattern
            pattern_record = {
                "pattern_type": pattern_type,
                "domain": domain,
                "description": description,
                "context": context or {},
                "action": action,
                "outcome": outcome,
                "embedding": embedding,
                "metadata": pattern_metadata,
                "created_by": created_by
            }

            response = self.supabase.table("archon_patterns").insert(
                pattern_record
            ).execute()

            if not response.data:
                raise Exception("Pattern creation returned no data")

            pattern = response.data[0]
            logger.info(f"Created pattern: {pattern['id']} - {description}")

            return pattern

        except Exception as e:
            logger.error(f"Failed to create pattern: {e}", exc_info=True)
            raise

    async def get_pattern(self, pattern_id: UUID) -> Optional[dict]:
        """Get a pattern by ID with observation count."""
        try:
            response = self.supabase.table("archon_patterns").select(
                "*"
            ).eq("id", str(pattern_id)).execute()

            if not response.data:
                return None

            pattern = response.data[0]

            # Get observation count
            obs_response = self.supabase.table("archon_pattern_observations").select(
                "id", count="exact"
            ).eq("pattern_id", str(pattern_id)).execute()

            pattern["observation_count"] = obs_response.count or 0

            return pattern

        except Exception as e:
            logger.error(f"Failed to get pattern: {e}", exc_info=True)
            raise

    async def list_patterns(
        self,
        pattern_type: str = None,
        domain: str = None,
        limit: int = 50
    ) -> list[dict]:
        """List patterns with optional filters."""
        try:
            query = self.supabase.table("archon_patterns").select("*")

            if pattern_type:
                query = query.eq("pattern_type", pattern_type)
            if domain:
                query = query.eq("domain", domain)

            query = query.order("created_at", desc=True).limit(limit)

            response = query.execute()
            return response.data or []

        except Exception as e:
            logger.error(f"Failed to list patterns: {e}", exc_info=True)
            raise

    async def search_patterns_semantic(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.7
    ) -> list[dict]:
        """
        Search patterns by semantic similarity.

        Args:
            query: Search query text
            limit: Maximum results
            threshold: Minimum similarity (0-1)

        Returns:
            List of patterns ranked by similarity
        """
        try:
            # Generate embedding for query
            query_embedding = await self.embedding_service.generate_embedding(query)

            if not query_embedding:
                return []

            # Call database function
            response = self.supabase.rpc(
                "search_patterns_semantic",
                {
                    "p_query_embedding": query_embedding,
                    "p_limit": limit,
                    "p_threshold": threshold
                }
            ).execute()

            return response.data or []

        except Exception as e:
            logger.error(f"Failed to search patterns: {e}", exc_info=True)
            raise

    async def record_observation(
        self,
        pattern_id: UUID,
        session_id: UUID = None,
        success_rating: int = 3,
        feedback: str = None,
        metadata: dict = None
    ) -> dict:
        """
        Record an observation of pattern application.

        Args:
            pattern_id: Pattern that was applied
            session_id: Session where it was applied (optional)
            success_rating: 1-5 rating (5 = very successful)
            feedback: Notes about the outcome
            metadata: Additional context

        Returns:
            Created observation dictionary
        """
        try:
            observation_record = {
                "pattern_id": str(pattern_id),
                "session_id": str(session_id) if session_id else None,
                "success_rating": success_rating,
                "feedback": feedback,
                "metadata": metadata or {}
            }

            response = self.supabase.table("archon_pattern_observations").insert(
                observation_record
            ).execute()

            if not response.data:
                raise Exception("Observation creation returned no data")

            observation = response.data[0]

            # Update pattern confidence score
            await self._update_pattern_confidence(pattern_id)

            logger.info(f"Recorded observation for pattern {pattern_id}: rating {success_rating}")

            return observation

        except Exception as e:
            logger.error(f"Failed to record observation: {e}", exc_info=True)
            raise

    async def get_pattern_confidence(self, pattern_id: UUID) -> dict:
        """
        Calculate confidence metrics for a pattern.

        Returns:
            {
                "confidence_score": float (0-1),
                "applications": int,
                "success_rate": float (0-1),
                "avg_rating": float (1-5)
            }
        """
        try:
            # Get all observations
            response = self.supabase.table("archon_pattern_observations").select(
                "success_rating"
            ).eq("pattern_id", str(pattern_id)).execute()

            observations = response.data or []

            if not observations:
                return {
                    "confidence_score": 0.0,
                    "applications": 0,
                    "success_rate": 0.0,
                    "avg_rating": 0.0
                }

            # Calculate metrics
            applications = len(observations)
            ratings = [obs["success_rating"] for obs in observations]
            avg_rating = sum(ratings) / len(ratings)

            # Success rate: % of ratings >= 4
            successes = len([r for r in ratings if r >= 4])
            success_rate = successes / applications

            # Confidence score: weighted by applications and success rate
            # More applications = higher confidence, capped at 0.95
            application_factor = min(applications / 20, 0.95)
            confidence_score = (success_rate * 0.7) + (application_factor * 0.3)

            return {
                "confidence_score": round(confidence_score, 2),
                "applications": applications,
                "success_rate": round(success_rate, 2),
                "avg_rating": round(avg_rating, 2)
            }

        except Exception as e:
            logger.error(f"Failed to calculate confidence: {e}", exc_info=True)
            raise

    async def _update_pattern_confidence(self, pattern_id: UUID):
        """Internal: Update pattern metadata with latest confidence scores."""
        try:
            metrics = await self.get_pattern_confidence(pattern_id)

            # Update pattern metadata
            await self.supabase.table("archon_patterns").update({
                "metadata": {
                    "confidence_score": metrics["confidence_score"],
                    "applications": metrics["applications"],
                    "success_rate": metrics["success_rate"],
                    "avg_rating": metrics["avg_rating"]
                }
            }).eq("id", str(pattern_id)).execute()

        except Exception as e:
            logger.error(f"Failed to update pattern confidence: {e}", exc_info=True)
            # Don't raise - this is a background update

    async def recommend_patterns(
        self,
        context: dict,
        limit: int = 5,
        min_confidence: float = 0.6
    ) -> list[dict]:
        """
        Recommend patterns based on current context.

        Args:
            context: Current situation (domain, task_type, etc.)
            limit: Maximum recommendations
            min_confidence: Minimum confidence threshold

        Returns:
            List of recommended patterns with confidence scores
        """
        try:
            # Build search query from context
            query_parts = []
            if "domain" in context:
                query_parts.append(context["domain"])
            if "task_type" in context:
                query_parts.append(context["task_type"])
            if "description" in context:
                query_parts.append(context["description"])

            query = " ".join(query_parts)

            # Search semantically similar patterns
            patterns = await self.search_patterns_semantic(
                query=query,
                limit=limit * 2,  # Get more to filter
                threshold=0.6
            )

            # Filter by confidence and sort
            recommended = []
            for pattern in patterns:
                metadata = pattern.get("metadata", {})
                confidence = metadata.get("confidence_score", 0.0)

                if confidence >= min_confidence:
                    pattern["recommendation_confidence"] = confidence
                    recommended.append(pattern)

            # Sort by confidence and limit
            recommended.sort(key=lambda p: p["recommendation_confidence"], reverse=True)

            return recommended[:limit]

        except Exception as e:
            logger.error(f"Failed to recommend patterns: {e}", exc_info=True)
            raise


# Singleton instance
_pattern_service = None

def get_pattern_service() -> PatternService:
    """Get or create the pattern service singleton."""
    global _pattern_service
    if _pattern_service is None:
        _pattern_service = PatternService()
    return _pattern_service
```

---

## Step 3: Write Unit Tests (1-2 hours)

### File to Create
```
python/tests/services/test_pattern_service.py
```

### Key Tests

```python
import pytest
from src.server.services.pattern_service import PatternService

@pytest.fixture
async def pattern_service():
    return PatternService()

@pytest.mark.asyncio
async def test_create_pattern(pattern_service):
    """Test pattern creation"""
    pattern = await pattern_service.create_pattern(
        pattern_type="technical",
        domain="database",
        description="Query optimization via indexing",
        action="Add B-tree index on queried columns",
        outcome="60% query time reduction"
    )

    assert pattern["pattern_type"] == "technical"
    assert pattern["domain"] == "database"
    assert pattern["embedding"] is not None

@pytest.mark.asyncio
async def test_record_observation(pattern_service):
    """Test observation recording"""
    # Create pattern first
    pattern = await pattern_service.create_pattern(
        pattern_type="technical",
        domain="test",
        description="Test pattern",
        action="Test action"
    )

    # Record observation
    obs = await pattern_service.record_observation(
        pattern_id=pattern["id"],
        success_rating=5,
        feedback="Worked great!"
    )

    assert obs["success_rating"] == 5

    # Check confidence updated
    confidence = await pattern_service.get_pattern_confidence(pattern["id"])
    assert confidence["applications"] == 1

@pytest.mark.asyncio
async def test_pattern_search(pattern_service):
    """Test semantic pattern search"""
    # Create test patterns
    await pattern_service.create_pattern(
        pattern_type="technical",
        domain="database",
        description="Database indexing for performance",
        action="Create indexes"
    )

    # Search
    results = await pattern_service.search_patterns_semantic(
        query="optimize database queries",
        limit=5
    )

    assert len(results) > 0
    assert "similarity" in results[0]
```

---

## Step 4: Integration Verification (30 min)

### Manual Testing

```python
# Test in Python REPL or Jupyter
from src.server.services.pattern_service import get_pattern_service
import asyncio

async def test():
    service = get_pattern_service()

    # Create a pattern
    pattern = await service.create_pattern(
        pattern_type="success",
        domain="development",
        description="Breaking large tasks into subtasks",
        action="Decompose into 5-10 actionable items",
        outcome="Better completion rate",
        created_by="claude"
    )

    print(f"Created: {pattern['id']}")

    # Search for it
    results = await service.search_patterns_semantic(
        "how to handle big tasks"
    )

    print(f"Found {len(results)} similar patterns")

asyncio.run(test())
```

---

## Success Criteria

- [x] Migration executed successfully (split into 005 + 006 — ivfflat caused rollbacks)
- [x] `archon_patterns` table exists with correct schema
- [x] `archon_pattern_observations` table exists
- [x] `search_patterns_semantic` function created
- [x] PatternService class implemented (`python/src/server/services/pattern_service.py`)
- [x] All service methods working
- [x] Unit tests passing (21/21 — `tests/server/services/test_pattern_service.py`)
- [x] Can create, retrieve, and search patterns ✅
- [x] Observation count and average_rating tracked correctly ✅
- Note: Semantic search returns empty (embedding=null) until Anthropic API key configured

---

## Estimated Time Breakdown

- Migration 004: 10 minutes
- PatternService implementation: 2 hours
- Unit tests: 1 hour
- Integration testing: 30 minutes

**Total: 3-4 hours**

---

## Next Steps After Day 1

**Day 2:**
- Create API endpoints for patterns
- Test endpoints with curl/Postman

**Day 3:**
- Create MCP tools for pattern management
- Test from Claude Code

---

## Troubleshooting

### Migration 004 Errors

**Error: "relation archon_sessions does not exist"**
- Solution: Migration 004 depends on migration 002
- Verify: Migration 002 was run successfully

**Error: "type vector does not exist"**
- Solution: Enable pgvector extension
- Run: `CREATE EXTENSION IF NOT EXISTS vector;`

### Service Implementation Issues

**Import errors:**
- Check: EmbeddingService exists and works
- Check: Supabase client accessible

**Embedding generation fails:**
- Check: Anthropic API key configured
- Or: Use alternative embedding provider

---

**Status:** Ready to start
**Next:** Run migration 004 and create PatternService
