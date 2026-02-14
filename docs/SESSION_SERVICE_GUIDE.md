# SessionService Usage Guide

**Version:** 1.0
**Date:** 2026-02-14
**Phase:** Phase 2 Day 2
**Purpose:** Complete guide to using SessionService for short-term memory management

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Core Concepts](#core-concepts)
4. [API Reference](#api-reference)
5. [Common Workflows](#common-workflows)
6. [Integration Patterns](#integration-patterns)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### What is SessionService?

SessionService is Archon's **short-term memory layer** that bridges the gap between:
- **Working Memory** (current context) - what the agent is doing right now
- **Long-Term Memory** (persistent knowledge) - what the agent remembers forever

It tracks agent work sessions, logs events, and enables:
- ✅ Temporal context ("What did I do in the last 7 days?")
- ✅ Semantic search ("Find sessions about database migration")
- ✅ Session resumption ("Continue from where I left off")
- ✅ Pattern learning (Day 5+ - AI summarization)

### Why Sessions?

Sessions represent **continuous work periods** by agents (claude, gemini, gpt, user). Each session:
- Has a start and end time
- Contains multiple events (task_created, decision_made, error_encountered, etc.)
- Can be linked to a project
- Can be summarized (manually or via AI)
- Is searchable via semantic similarity

### Architecture

```
┌─────────────────────────────────────────────┐
│           Your Application                   │
├─────────────────────────────────────────────┤
│         SessionService (Singleton)           │
│  ┌────────────────┐   ┌─────────────────┐  │
│  │ EmbeddingService│   │ Supabase Client │  │
│  └────────────────┘   └─────────────────┘  │
├─────────────────────────────────────────────┤
│              Database Layer                  │
│  ┌──────────────────┐  ┌──────────────────┐│
│  │ archon_sessions  │  │ archon_session_  ││
│  │                  │  │ events           ││
│  └──────────────────┘  └──────────────────┘│
└─────────────────────────────────────────────┘
```

---

## Quick Start

### 1. Get Service Instance

```python
from src.server.services.session_service import get_session_service

# Get singleton instance
service = get_session_service()
```

### 2. Create a Session

```python
from uuid import UUID

# Basic session
session = await service.create_session(
    agent="claude",
    metadata={"context": "implementing feature X"}
)

# Session linked to project
session = await service.create_session(
    agent="claude",
    project_id=UUID("b231255f-6ed9-4440-80de-958bcf7b4f9f"),
    metadata={"phase": "Phase 2", "day": 1}
)

print(f"Session started: {session['id']}")
```

### 3. Log Events

```python
# Log task creation
await service.add_event(
    session_id=session["id"],
    event_type="task_created",
    event_data={
        "task_id": "123",
        "title": "Implement SessionService"
    }
)

# Log decision
await service.add_event(
    session_id=session["id"],
    event_type="decision_made",
    event_data={
        "decision": "use pgvector for semantic search",
        "rationale": "industry standard, efficient"
    }
)
```

### 4. End Session

```python
# End with summary
await service.end_session(
    session_id=session["id"],
    summary="Completed SessionService implementation with 12 methods, tests, and documentation"
)
```

### 5. Search Sessions

```python
# Semantic search
results = await service.search_sessions(
    query="database migration errors",
    limit=5,
    threshold=0.7
)

for result in results:
    print(f"{result['similarity']:.2f}: {result['summary']}")
```

---

## Core Concepts

### Agents

Sessions are created by **agents**. Valid values:
- `"claude"` - Claude (Anthropic)
- `"gemini"` - Gemini (Google)
- `"gpt"` - GPT (OpenAI)
- `"user"` - Human user

This enables multi-agent coordination and context sharing.

### Event Types

Sessions contain **events** that represent actions taken during the session:

| Event Type | Purpose | Example Data |
|------------|---------|--------------|
| `task_created` | Agent created a task | `{"task_id": "123", "title": "..."}` |
| `task_updated` | Agent updated a task | `{"task_id": "123", "changes": {...}}` |
| `task_completed` | Agent completed a task | `{"task_id": "123", "outcome": "success"}` |
| `decision_made` | Agent made a decision | `{"decision": "...", "rationale": "..."}` |
| `error_encountered` | Error occurred | `{"error": "...", "context": "..."}` |
| `pattern_identified` | Pattern recognized | `{"pattern": "...", "instances": [...]}` |
| `context_shared` | Context shared with another agent | `{"agent": "gemini", "context": {...}}` |

You can define custom event types as needed.

### Metadata

Sessions and events can have **metadata** (JSONB):

**Session Metadata (after summarization):**
```json
{
  "key_events": ["migration_created", "tables_created"],
  "decisions": ["use pgvector", "async/await pattern"],
  "outcomes": ["database ready", "tests passing"],
  "next_steps": ["implement API endpoints", "create frontend"]
}
```

**Event Metadata:**
```json
{
  "file": "session_service.py",
  "lines_changed": 450,
  "complexity": "high"
}
```

### Embeddings

Sessions and events are automatically **embedded** using OpenAI's text-embedding-3-small (1536 dimensions):

- **Session embeddings**: Generated from summary + metadata key_events
- **Event embeddings**: Generated from event_type + event_data

This enables semantic search across all sessions and events.

---

## API Reference

### Session Management

#### `create_session()`

Create a new agent session.

```python
async def create_session(
    agent: str,
    project_id: Optional[UUID] = None,
    metadata: Optional[dict] = None
) -> dict:
    """
    Args:
        agent: Agent identifier (claude, gemini, gpt, user)
        project_id: Optional UUID of associated project
        metadata: Optional additional context

    Returns:
        Created session dictionary with id, agent, started_at, etc.
    """
```

**Example:**
```python
session = await service.create_session(
    agent="claude",
    project_id=UUID("..."),
    metadata={"phase": "Phase 2", "day": 1}
)
```

#### `end_session()`

End a session and optionally add a summary.

```python
async def end_session(
    session_id: UUID,
    summary: Optional[str] = None
) -> dict:
    """
    Args:
        session_id: UUID of session to end
        summary: Optional summary text (can be AI-generated later)

    Returns:
        Updated session with ended_at and embedding (if summary provided)
    """
```

**Example:**
```python
ended = await service.end_session(
    session_id=session["id"],
    summary="Completed database migration with 10 new tables and semantic search"
)
```

#### `get_session()`

Get a session with all its events.

```python
async def get_session(session_id: UUID) -> Optional[dict]:
    """
    Args:
        session_id: UUID of session to retrieve

    Returns:
        Session dictionary with events list, or None if not found
    """
```

**Example:**
```python
session = await service.get_session(UUID("..."))
print(f"Events: {len(session['events'])}")
for event in session['events']:
    print(f"  - {event['event_type']} at {event['timestamp']}")
```

#### `list_sessions()`

List recent sessions with optional filters.

```python
async def list_sessions(
    agent: Optional[str] = None,
    project_id: Optional[UUID] = None,
    since: Optional[datetime] = None,
    limit: int = 20
) -> list[dict]:
    """
    Args:
        agent: Filter by agent name
        project_id: Filter by project UUID
        since: Filter sessions started after this datetime
        limit: Maximum number of sessions to return (default: 20)

    Returns:
        List of session dictionaries (without events)
    """
```

**Examples:**
```python
# Last 10 sessions for claude
sessions = await service.list_sessions(agent="claude", limit=10)

# Sessions from last 7 days
from datetime import datetime, timedelta, timezone
week_ago = datetime.now(timezone.utc) - timedelta(days=7)
sessions = await service.list_sessions(since=week_ago)

# Sessions for specific project
sessions = await service.list_sessions(project_id=UUID("..."))
```

### Event Management

#### `add_event()`

Log an event to a session.

```python
async def add_event(
    session_id: UUID,
    event_type: str,
    event_data: dict
) -> dict:
    """
    Args:
        session_id: UUID of parent session
        event_type: Type of event (see event types above)
        event_data: Event-specific data (JSON)

    Returns:
        Created event dictionary with embedding
    """
```

**Example:**
```python
event = await service.add_event(
    session_id=session["id"],
    event_type="task_created",
    event_data={
        "task_id": "123",
        "title": "Implement SessionService",
        "assignee": "claude",
        "priority": "high"
    }
)
```

### Semantic Search

#### `search_sessions()`

Search sessions using semantic similarity.

```python
async def search_sessions(
    query: str,
    limit: int = 10,
    threshold: float = 0.7
) -> list[dict]:
    """
    Args:
        query: Search query text
        limit: Maximum results to return
        threshold: Minimum similarity score (0-1, default 0.7)

    Returns:
        List of matching sessions with similarity scores
    """
```

**Example:**
```python
# Find sessions about database work
results = await service.search_sessions(
    query="database migration and schema changes",
    limit=5,
    threshold=0.75
)

for result in results:
    print(f"Similarity: {result['similarity']:.2%}")
    print(f"Summary: {result['summary']}")
    print(f"Agent: {result['agent']}")
    print(f"Started: {result['started_at']}")
    print("---")
```

### Temporal Queries

#### `get_last_session()`

Get the most recent session for an agent (for resuming context).

```python
async def get_last_session(agent: str) -> Optional[dict]:
    """
    Args:
        agent: Agent identifier

    Returns:
        Most recent session with events, or None
    """
```

**Example:**
```python
# Resume from last session
last = await service.get_last_session("claude")
if last:
    print(f"Last session: {last['summary']}")
    print(f"Ended: {last['ended_at']}")
    print(f"Events: {len(last['events'])}")
```

#### `count_sessions()`

Count sessions for an agent in the last N days.

```python
async def count_sessions(
    agent: str,
    days: int = 30
) -> int:
    """
    Args:
        agent: Agent identifier
        days: Number of days to look back (default: 30)

    Returns:
        Number of sessions
    """
```

**Example:**
```python
# Activity metrics
week_count = await service.count_sessions("claude", days=7)
month_count = await service.count_sessions("claude", days=30)

print(f"Sessions this week: {week_count}")
print(f"Sessions this month: {month_count}")
```

#### `get_recent_sessions()`

Get recent sessions using optimized database function.

```python
async def get_recent_sessions(
    agent: str,
    days: int = 7,
    limit: int = 20
) -> list[dict]:
    """
    Args:
        agent: Agent identifier
        days: Number of days to look back (default: 7)
        limit: Maximum sessions to return (default: 20)

    Returns:
        List of recent sessions with event_count field
    """
```

**Example:**
```python
recent = await service.get_recent_sessions("claude", days=7)
for session in recent:
    print(f"{session['started_at']}: {session['event_count']} events")
```

### Summary Management

#### `update_session_summary()`

Update a session's summary and metadata (used after AI summarization).

```python
async def update_session_summary(
    session_id: UUID,
    summary: str,
    metadata: Optional[dict] = None
) -> dict:
    """
    Args:
        session_id: UUID of session to update
        summary: Summary text
        metadata: Optional metadata (key_events, decisions, outcomes, next_steps)

    Returns:
        Updated session with new embedding
    """
```

**Example:**
```python
# After AI generates summary
updated = await service.update_session_summary(
    session_id=session["id"],
    summary="Completed Phase 2 Day 1 with database schema migration...",
    metadata={
        "key_events": ["migration_created", "tables_created", "indexes_added"],
        "decisions": ["use pgvector", "IVFFlat indexes"],
        "outcomes": ["database ready", "semantic search enabled"],
        "next_steps": ["implement SessionService", "create API endpoints"]
    }
)
```

#### `get_active_sessions()`

Get all currently active (not ended) sessions.

```python
async def get_active_sessions() -> list[dict]:
    """
    Returns:
        List of active session dictionaries
    """
```

**Example:**
```python
active = await service.get_active_sessions()
print(f"Currently active: {len(active)} sessions")
for session in active:
    print(f"  - {session['agent']} (started {session['started_at']})")
```

---

## Common Workflows

### Workflow 1: Basic Session

```python
from src.server.services.session_service import get_session_service

service = get_session_service()

# 1. Start session
session = await service.create_session(
    agent="claude",
    metadata={"task": "bug fix"}
)

# 2. Log work
await service.add_event(
    session_id=session["id"],
    event_type="error_encountered",
    event_data={"error": "TypeError in line 42"}
)

await service.add_event(
    session_id=session["id"],
    event_type="decision_made",
    event_data={"decision": "add type validation"}
)

# 3. End session
await service.end_session(
    session_id=session["id"],
    summary="Fixed TypeError by adding validation to parse_input() function"
)
```

### Workflow 2: Project-Linked Session

```python
from uuid import UUID

# Get project ID from Archon
project_id = UUID("b231255f-6ed9-4440-80de-958bcf7b4f9f")

# Start session for project
session = await service.create_session(
    agent="claude",
    project_id=project_id,
    metadata={"phase": "Phase 2", "day": 2}
)

# Log implementation events
await service.add_event(
    session_id=session["id"],
    event_type="task_created",
    event_data={
        "task_id": "...",
        "title": "Implement SessionService",
        "feature": "Short-Term Memory"
    }
)

# ... work ...

# End with detailed summary
await service.end_session(
    session_id=session["id"],
    summary="Implemented SessionService with 12 methods, comprehensive tests, and usage documentation"
)
```

### Workflow 3: Context Resumption

```python
# Get last session to resume context
last = await service.get_last_session("claude")

if last:
    print(f"Resuming from: {last['summary']}")

    # Check what was being worked on
    for event in last['events'][-5:]:  # Last 5 events
        if event['event_type'] == 'task_created':
            print(f"  - Working on: {event['event_data']['title']}")

    # Start new session with context
    new_session = await service.create_session(
        agent="claude",
        project_id=last.get('project_id'),
        metadata={
            "previous_session": str(last['id']),
            "context": "continuing from previous work"
        }
    )
```

### Workflow 4: Semantic Memory Search

```python
# User asks: "What have I done about database migrations?"
results = await service.search_sessions(
    query="database migration schema changes",
    limit=5,
    threshold=0.7
)

if results:
    print(f"Found {len(results)} relevant sessions:")
    for r in results:
        print(f"\n{r['similarity']:.0%} match - {r['started_at']}")
        print(f"Agent: {r['agent']}")
        print(f"Summary: {r['summary']}")
else:
    print("No relevant sessions found")
```

### Workflow 5: Activity Analytics

```python
from datetime import datetime, timedelta, timezone

# Last 7 days activity
week_sessions = await service.get_recent_sessions("claude", days=7)
week_count = len(week_sessions)
total_events = sum(s['event_count'] for s in week_sessions)

print(f"Activity Report (Last 7 Days)")
print(f"  Sessions: {week_count}")
print(f"  Events: {total_events}")
print(f"  Avg events/session: {total_events/week_count:.1f}")

# Most active day
by_day = {}
for session in week_sessions:
    day = session['started_at'].split('T')[0]
    by_day[day] = by_day.get(day, 0) + 1

most_active = max(by_day.items(), key=lambda x: x[1])
print(f"  Most active day: {most_active[0]} ({most_active[1]} sessions)")
```

---

## Integration Patterns

### Pattern 1: API Endpoint Integration

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import UUID

router = APIRouter(prefix="/api/sessions")

class CreateSessionRequest(BaseModel):
    agent: str
    project_id: Optional[UUID] = None
    metadata: Optional[dict] = None

@router.post("/")
async def create_session(req: CreateSessionRequest):
    """Create a new session."""
    try:
        session = await get_session_service().create_session(
            agent=req.agent,
            project_id=req.project_id,
            metadata=req.metadata
        )
        return {"success": True, "session": session}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Pattern 2: MCP Tool Integration

```python
# MCP tool for creating sessions
@mcp_server.tool()
async def archon_create_session(
    agent: str,
    project_id: Optional[str] = None,
    metadata: Optional[dict] = None
) -> dict:
    """Create a new Archon session for tracking agent work."""
    project_uuid = UUID(project_id) if project_id else None

    session = await get_session_service().create_session(
        agent=agent,
        project_id=project_uuid,
        metadata=metadata
    )

    return {
        "success": True,
        "session_id": str(session["id"]),
        "agent": session["agent"],
        "started_at": session["started_at"]
    }
```

### Pattern 3: Frontend Integration (React)

```typescript
// Using TanStack Query v5
import { useMutation, useQuery } from '@tanstack/react-query';

// Hook for creating session
export function useCreateSession() {
  return useMutation({
    mutationFn: async (data: {
      agent: string;
      project_id?: string;
      metadata?: Record<string, any>;
    }) => {
      const res = await fetch('/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error('Failed to create session');
      return res.json();
    },
  });
}

// Hook for searching sessions
export function useSearchSessions(query: string) {
  return useQuery({
    queryKey: ['sessions', 'search', query],
    queryFn: async () => {
      const res = await fetch(`/api/sessions/search?q=${encodeURIComponent(query)}`);
      if (!res.ok) throw new Error('Search failed');
      return res.json();
    },
    enabled: query.length >= 3,
  });
}
```

### Pattern 4: Background Task Integration

```python
import asyncio

async def session_lifecycle_task(agent: str, work_fn):
    """Wrapper that automatically creates/ends sessions for background tasks."""
    service = get_session_service()

    # Start session
    session = await service.create_session(
        agent=agent,
        metadata={"task_type": "background"}
    )

    try:
        # Do work
        result = await work_fn(session["id"])

        # End with success
        await service.end_session(
            session_id=session["id"],
            summary=f"Background task completed successfully: {result}"
        )

    except Exception as e:
        # Log error
        await service.add_event(
            session_id=session["id"],
            event_type="error_encountered",
            event_data={"error": str(e), "traceback": traceback.format_exc()}
        )

        # End with failure summary
        await service.end_session(
            session_id=session["id"],
            summary=f"Background task failed: {str(e)}"
        )
        raise

# Usage
await session_lifecycle_task("claude", my_background_work)
```

---

## Best Practices

### 1. Session Granularity

**✅ DO:** Create sessions for logical work units
```python
# Good: One session per feature implementation
session = await service.create_session(
    agent="claude",
    metadata={"feature": "SessionService implementation"}
)
```

**❌ DON'T:** Create too many micro-sessions
```python
# Bad: New session for every small action
session1 = await service.create_session(agent="claude")  # Read file
session2 = await service.create_session(agent="claude")  # Edit file
session3 = await service.create_session(agent="claude")  # Save file
```

### 2. Event Logging

**✅ DO:** Log significant events
```python
# Important milestones
await service.add_event(
    session_id=session["id"],
    event_type="task_completed",
    event_data={"task_id": "123", "outcome": "success", "tests_passed": 15}
)
```

**❌ DON'T:** Log every tiny action
```python
# Too granular
await service.add_event(session_id=session["id"], event_type="read_file", event_data={...})
await service.add_event(session_id=session["id"], event_type="cursor_moved", event_data={...})
```

### 3. Summaries

**✅ DO:** Write descriptive, searchable summaries
```python
await service.end_session(
    session_id=session["id"],
    summary="Implemented SessionService with 12 CRUD methods, semantic search using pgvector, "
            "and comprehensive test suite. Created session/event tables with embeddings. "
            "Integrated with EmbeddingService for automatic vector generation."
)
```

**❌ DON'T:** Write vague summaries
```python
await service.end_session(
    session_id=session["id"],
    summary="Did some work"  # Not searchable or useful
)
```

### 4. Error Handling

**✅ DO:** Always handle exceptions
```python
try:
    session = await service.create_session(agent="claude")
except Exception as e:
    logger.error(f"Failed to create session: {e}")
    # Fallback or retry logic
```

**✅ DO:** Log errors as events
```python
try:
    result = await risky_operation()
except ValueError as e:
    await service.add_event(
        session_id=session["id"],
        event_type="error_encountered",
        event_data={
            "error_type": "ValueError",
            "message": str(e),
            "operation": "risky_operation"
        }
    )
```

### 5. Search Queries

**✅ DO:** Use descriptive, concept-based queries
```python
# Good - describes what you're looking for
results = await service.search_sessions(
    query="database schema migration with vector embeddings and semantic search",
    threshold=0.7
)
```

**❌ DON'T:** Use single keywords
```python
# Bad - too vague
results = await service.search_sessions(query="database")
```

### 6. Metadata Structure

**✅ DO:** Use consistent metadata schemas
```python
# Standardized structure
metadata = {
    "phase": "Phase 2",
    "day": 2,
    "feature": "SessionService",
    "complexity": "high",
    "estimated_hours": 4
}
```

**❌ DON'T:** Use inconsistent keys
```python
# Bad - no standard
metadata1 = {"p": "2", "d": "2"}
metadata2 = {"phase_num": 2, "day_of_phase": 2}
```

### 7. Cleanup

**✅ DO:** End sessions when work completes
```python
# Always end sessions
await service.end_session(session_id=session["id"], summary="...")
```

**❌ DON'T:** Leave sessions hanging
```python
# Bad - session never ended
session = await service.create_session(agent="claude")
# ... work ...
# Forgot to call end_session()
```

---

## Troubleshooting

### Problem: "Session creation returned no data"

**Cause:** Database connection issue or RLS policy blocking insert

**Solution:**
```python
# Check Supabase connection
from src.server.config.database import get_supabase_client
client = get_supabase_client()
print(client.table("archon_sessions").select("count").execute())
```

### Problem: "Failed to generate query embedding"

**Cause:** OpenAI API key not set or invalid

**Solution:**
```bash
# Check environment variable
echo $OPENAI_API_KEY

# Set if missing
export OPENAI_API_KEY="sk-..."
```

### Problem: Search returns no results

**Cause 1:** Threshold too high

**Solution:** Lower threshold
```python
# Try lower threshold
results = await service.search_sessions(query="...", threshold=0.5)
```

**Cause 2:** No sessions have summaries yet

**Solution:** Sessions need summaries to be searchable
```python
# Check if sessions have embeddings
sessions = await service.list_sessions(limit=10)
has_embeddings = sum(1 for s in sessions if s.get('embedding'))
print(f"{has_embeddings}/{len(sessions)} have embeddings")
```

### Problem: Events not appearing in get_session()

**Cause:** Events created for wrong session_id

**Solution:** Verify session ID
```python
session = await service.get_session(session_id)
if not session:
    print("Session not found!")
else:
    print(f"Session has {len(session['events'])} events")
```

### Problem: Performance degradation with many sessions

**Cause:** Missing indexes or unoptimized queries

**Solution:** Check migration was run correctly
```sql
-- Verify indexes exist
SELECT indexname FROM pg_indexes
WHERE tablename IN ('archon_sessions', 'archon_session_events');
```

---

## Next Steps

After mastering SessionService:

1. **Day 3:** Create REST API endpoints and MCP tools
2. **Day 4:** Expand semantic search to tasks and projects
3. **Day 5:** Implement AI summarization with PydanticAI
4. **Day 6-7:** Build frontend session views
5. **Day 8:** Integration testing and documentation

---

## Reference

### Related Files
- **Implementation:** `python/src/server/services/session_service.py`
- **Tests:** `python/tests/services/test_session_service.py`
- **Embeddings:** `python/src/server/utils/embeddings.py`
- **Migration:** `migration/002_session_memory.sql`
- **Verification:** `migration/verify_002_migration.sql`

### Related Documentation
- Phase 2 Roadmap: `docs/PHASE_2_ROADMAP.md`
- Memory Layer Mapping: `docs/MEMORY_LAYER_MAPPING.md`
- Migration Guide: `docs/RUN_MIGRATION_002.md`

---

**Created By:** Claude (Archon Agent)
**Date:** 2026-02-14
**Project:** Shared Memory System Implementation
**Phase:** Phase 2 Day 2
