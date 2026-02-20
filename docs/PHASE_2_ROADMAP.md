# Phase 2: Session Memory & Semantic Search - Implementation Roadmap

**Timeline:** Week 2 (5-8 days)
**Goal:** Close the 15% short-term memory gap identified in Week 1
**Target:** Bring Archon from 75% → 90% memory system completion

---

## Executive Summary

Phase 1 (Week 1) revealed that **short-term memory is the critical gap**. Archon has excellent working memory (90%) and long-term memory (95%), but weak short-term memory (40%).

**Phase 2 will implement:**
1. Session tracking system
2. Semantic search across all memory layers
3. Temporal query capabilities
4. Session summarization

**Expected Outcome:** Complete short-term memory layer, enabling agents to:
- Resume from previous sessions with full context
- Query "What happened in the last 7 days?"
- Search for similar past work semantically
- Build temporal context automatically

---

## Current State (End of Week 1)

### ✅ Completed (Week 1)
- [x] MCP connection verified and documented
- [x] 5 MCP tools tested (2 working, 3 broken but workaround exists)
- [x] Complete tool inventory created (7 Archon + 40+ GitHub tools)
- [x] Memory layer mapping completed
- [x] Gap analysis: 75% overall (90% working, 40% short-term, 95% long-term)

### 📋 Week 1 Remaining (Optional)
- [ ] Task 7: Baseline performance metrics (assigned to user)
- [ ] Task 8: Multi-agent scenario test (assigned to user)

**Decision:** Can proceed to Phase 2 with 75% Week 1 completion. Tasks 7-8 are informational, not blockers.

---

## Phase 2 Implementation Plan

### Day 1-2: Database Schema & Session Management

#### Database Tables

**1. archon_sessions Table**
```sql
CREATE TABLE archon_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent VARCHAR(50) NOT NULL,
  project_id UUID REFERENCES archon_projects(id),
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ended_at TIMESTAMPTZ,
  summary TEXT,
  context JSONB DEFAULT '{}',
  embedding VECTOR(1536),
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sessions_agent ON archon_sessions(agent);
CREATE INDEX idx_sessions_project ON archon_sessions(project_id);
CREATE INDEX idx_sessions_started ON archon_sessions(started_at DESC);
CREATE INDEX idx_sessions_embedding ON archon_sessions USING ivfflat (embedding vector_cosine_ops);
```

**2. archon_session_events Table**
```sql
CREATE TABLE archon_session_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES archon_sessions(id) ON DELETE CASCADE,
  event_type VARCHAR(50) NOT NULL,
  event_data JSONB NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  embedding VECTOR(1536),
  metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_events_session ON archon_session_events(session_id);
CREATE INDEX idx_events_type ON archon_session_events(event_type);
CREATE INDEX idx_events_timestamp ON archon_session_events(timestamp DESC);
CREATE INDEX idx_events_embedding ON archon_session_events USING ivfflat (embedding vector_cosine_ops);
```

**3. Add embeddings to existing tables**
```sql
-- Add embeddings to tasks for semantic search
ALTER TABLE archon_tasks ADD COLUMN embedding VECTOR(1536);
CREATE INDEX idx_tasks_embedding ON archon_tasks USING ivfflat (embedding vector_cosine_ops);

-- Add embeddings to projects
ALTER TABLE archon_projects ADD COLUMN embedding VECTOR(1536);
CREATE INDEX idx_projects_embedding ON archon_projects USING ivfflat (embedding vector_cosine_ops);
```

**Event Types:**
- `task_created` - Task creation
- `task_updated` - Task status/content change
- `task_completed` - Task completion
- `decision_made` - Agent decision point
- `error_encountered` - Error occurred
- `pattern_identified` - Pattern recognized
- `context_shared` - Context shared with another agent

#### Python Service Layer

**File:** `python/src/server/services/session_service.py`

```python
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from ..config.database import get_supabase_client
from ..utils.embeddings import generate_embedding

class SessionService:
    def __init__(self):
        self.supabase = get_supabase_client()

    async def create_session(
        self,
        agent: str,
        project_id: Optional[UUID] = None,
        metadata: dict = None
    ):
        """Create a new agent session"""
        pass

    async def end_session(self, session_id: UUID, summary: Optional[str] = None):
        """End session and generate summary if not provided"""
        pass

    async def add_event(
        self,
        session_id: UUID,
        event_type: str,
        event_data: dict
    ):
        """Log event to session"""
        pass

    async def get_session(self, session_id: UUID):
        """Get session with events"""
        pass

    async def list_sessions(
        self,
        agent: Optional[str] = None,
        project_id: Optional[UUID] = None,
        since: Optional[datetime] = None,
        limit: int = 20
    ):
        """List recent sessions"""
        pass

    async def search_sessions(self, query: str, limit: int = 10):
        """Semantic search across sessions"""
        pass

    async def get_last_session(self, agent: str):
        """Get agent's most recent session"""
        pass

    async def summarize_session(self, session_id: UUID) -> str:
        """Generate AI summary of session"""
        # Use PydanticAI to generate summary
        pass
```

**Deliverables:**
- [x] Migration file: `python/migrations/002_session_tables.sql`
- [x] Service implementation: `python/src/server/services/session_service.py`
- [x] Unit tests: `python/tests/services/test_session_service.py`

---

### Day 3: API Endpoints & MCP Tools

#### REST API Endpoints

**File:** `python/src/server/api_routes/sessions_api.py`

```python
@router.post("/sessions")
async def create_session(request: CreateSessionRequest):
    """Create new agent session"""
    pass

@router.put("/sessions/{session_id}/end")
async def end_session(session_id: str, summary: Optional[str] = None):
    """End session with optional summary"""
    pass

@router.post("/sessions/{session_id}/events")
async def add_event(session_id: str, event: SessionEventRequest):
    """Log event to session"""
    pass

@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session details with events"""
    pass

@router.get("/sessions")
async def list_sessions(
    agent: Optional[str] = None,
    project_id: Optional[str] = None,
    since: Optional[str] = None,
    limit: int = 20
):
    """List recent sessions"""
    pass

@router.post("/sessions/search")
async def search_sessions(query: str, limit: int = 10):
    """Semantic search across sessions"""
    pass

@router.get("/sessions/last")
async def get_last_session(agent: str):
    """Get agent's most recent session"""
    pass

@router.post("/sessions/{session_id}/summarize")
async def summarize_session(session_id: str):
    """Generate AI summary"""
    pass
```

#### MCP Tools

**File:** `python/src/mcp_server/features/sessions/session_tools.py`

```python
@mcp_server.tool()
async def archon_create_session(
    agent: str,
    project_id: Optional[str] = None,
    metadata: Optional[dict] = None
) -> dict:
    """Create a new agent session for tracking work"""
    pass

@mcp_server.tool()
async def archon_end_session(
    session_id: str,
    summary: Optional[str] = None
) -> dict:
    """End current session with optional summary"""
    pass

@mcp_server.tool()
async def archon_get_last_session(agent: str) -> dict:
    """Get agent's most recent session to resume context"""
    pass

@mcp_server.tool()
async def archon_list_sessions(
    agent: Optional[str] = None,
    timeframe: Optional[str] = "7days",
    limit: int = 10
) -> dict:
    """List recent sessions for context building"""
    pass

@mcp_server.tool()
async def archon_search_sessions(
    query: str,
    limit: int = 10
) -> dict:
    """Semantic search across session history"""
    pass

@mcp_server.tool()
async def archon_add_session_event(
    session_id: str,
    event_type: str,
    event_data: dict
) -> dict:
    """Log significant event to current session"""
    pass
```

**Deliverables:**
- [x] API routes: `python/src/server/api_routes/sessions_api.py`
- [x] MCP tools: `python/src/mcp_server/features/sessions/session_tools.py`
- [x] Integration tests: `python/tests/api/test_sessions_api.py`

---

### Day 4: Semantic Search Expansion

#### Embedding Generation Service

**File:** `python/src/server/utils/embeddings.py`

```python
from typing import Optional
from openai import AsyncOpenAI

class EmbeddingService:
    def __init__(self):
        self.client = AsyncOpenAI()

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector for text"""
        response = await self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    async def generate_task_embedding(self, task: dict) -> list[float]:
        """Generate embedding for task (title + description)"""
        text = f"{task['title']} {task.get('description', '')}"
        return await self.generate_embedding(text)

    async def generate_session_embedding(self, session: dict) -> list[float]:
        """Generate embedding for session summary"""
        # Combine summary + key events
        pass

    async def generate_project_embedding(self, project: dict) -> list[float]:
        """Generate embedding for project"""
        # Combine title + description + features
        pass
```

#### Background Job for Embedding Generation

**File:** `python/src/server/jobs/embedding_generator.py`

```python
# Backfill embeddings for existing records
# Run on new task/project creation
# Regenerate on significant updates
```

#### Unified Memory Search

**File:** `python/src/server/services/memory_search_service.py`

```python
class MemorySearchService:
    async def search_all_layers(
        self,
        query: str,
        layers: list[str] = ["working", "short-term", "long-term"],
        timeframe: Optional[str] = None,
        limit: int = 20
    ):
        """
        Unified semantic search across all memory layers

        Layers:
        - working: Active tasks, current projects
        - short-term: Recent sessions (7-30 days)
        - long-term: Knowledge base, historical patterns

        Returns ranked results from all layers
        """
        pass
```

**New API Endpoint:**
```python
@router.post("/memory/search")
async def unified_memory_search(request: MemorySearchRequest):
    """Search across all memory layers semantically"""
    pass
```

**Deliverables:**
- [x] Embedding service: `python/src/server/utils/embeddings.py`
- [x] Background job: `python/src/server/jobs/embedding_generator.py`
- [x] Memory search service: `python/src/server/services/memory_search_service.py`
- [x] API endpoint: Add to `sessions_api.py` or new `memory_api.py`
- [x] Tests: `python/tests/services/test_memory_search.py`

---

### Day 5: Session Summarization with PydanticAI

#### AI Summary Agent

**File:** `python/src/agents/features/session_summarizer.py`

```python
from pydantic_ai import Agent
from pydantic import BaseModel

class SessionSummary(BaseModel):
    summary: str
    key_events: list[str]
    decisions_made: list[str]
    outcomes: list[str]
    next_steps: list[str]

session_summarizer = Agent(
    'openai:gpt-4',
    result_type=SessionSummary,
    system_prompt="""
    You are a session summarization agent for Archon.
    Given session events, create a concise summary focusing on:
    - What was accomplished
    - Key decisions made
    - Problems encountered
    - Next steps suggested
    """
)

async def summarize_session(session: dict, events: list[dict]) -> SessionSummary:
    """Generate structured summary of session"""
    context = {
        "session": session,
        "events": events,
        "event_count": len(events)
    }
    result = await session_summarizer.run(
        f"Summarize this agent session with {len(events)} events",
        context=context
    )
    return result.data
```

**Integration:**
```python
# In SessionService.summarize_session():
async def summarize_session(self, session_id: UUID) -> str:
    session = await self.get_session(session_id)
    events = session['events']

    summary = await summarize_session(session, events)

    # Update session with summary
    await self.supabase.table("archon_sessions").update({
        "summary": summary.summary,
        "metadata": {
            "key_events": summary.key_events,
            "decisions": summary.decisions_made,
            "outcomes": summary.outcomes,
            "next_steps": summary.next_steps
        }
    }).eq("id", session_id).execute()

    return summary.summary
```

**Deliverables:**
- [x] Summarizer agent: `python/src/agents/features/session_summarizer.py`
- [x] Integration with SessionService
- [x] Tests: `python/tests/agents/test_session_summarizer.py`

---

### Day 6-7: Frontend Integration

#### Session UI Components

**File:** `archon-ui-main/src/features/sessions/components/SessionCard.tsx`

```typescript
interface SessionCardProps {
  session: Session;
  onSelect: (id: string) => void;
}

export function SessionCard({ session, onSelect }: SessionCardProps) {
  return (
    <Card onClick={() => onSelect(session.id)}>
      <CardHeader>
        <div className="flex justify-between">
          <h3>{session.agent}</h3>
          <time>{formatDate(session.started_at)}</time>
        </div>
      </CardHeader>
      <CardContent>
        <p>{session.summary || "No summary yet"}</p>
        <div className="flex gap-2 mt-2">
          <Badge>{session.events?.length || 0} events</Badge>
          <Badge>{formatDuration(session.started_at, session.ended_at)}</Badge>
        </div>
      </CardContent>
    </Card>
  );
}
```

**File:** `archon-ui-main/src/features/sessions/views/SessionsView.tsx`

```typescript
export function SessionsView() {
  const { data: sessions } = useSessions({ timeframe: "7days" });

  return (
    <div className="container">
      <h1>Recent Sessions</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sessions?.map(session => (
          <SessionCard key={session.id} session={session} />
        ))}
      </div>
    </div>
  );
}
```

#### Memory Search UI

**File:** `archon-ui-main/src/features/memory/components/MemorySearch.tsx`

```typescript
export function MemorySearch() {
  const [query, setQuery] = useState("");
  const { mutate: search, data: results } = useMemorySearch();

  return (
    <div>
      <Input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search across all memory layers..."
      />
      <Button onClick={() => search({ query })}>Search</Button>

      {results && (
        <div className="mt-4 space-y-2">
          {results.working_memory.map(item => (
            <MemoryResult key={item.id} item={item} layer="working" />
          ))}
          {results.short_term.map(item => (
            <MemoryResult key={item.id} item={item} layer="short-term" />
          ))}
          {results.long_term.map(item => (
            <MemoryResult key={item.id} item={item} layer="long-term" />
          ))}
        </div>
      )}
    </div>
  );
}
```

**Deliverables:**
- [x] Session components: `archon-ui-main/src/features/sessions/`
- [x] Memory search component: `archon-ui-main/src/features/memory/`
- [x] TanStack Query hooks: `useSessions.ts`, `useMemorySearch.ts`
- [x] Routes: Add to `src/App.tsx`
- [x] Tests: Component tests for sessions

---

### Day 8: Testing & Documentation

#### Integration Tests

**Test Scenarios:**
1. Create session → Add events → End session → Verify summary
2. Search sessions semantically → Verify relevance
3. Resume from last session → Verify context loaded
4. Multi-agent: Agent A creates session, Agent B queries it
5. Temporal queries: "Last 7 days" filtering
6. Memory search across all layers

**File:** `python/tests/integration/test_session_workflow.py`

#### Documentation

**Files to Create:**
1. `docs/SESSION_SYSTEM_GUIDE.md` - User guide for sessions
2. `docs/MEMORY_SEARCH_GUIDE.md` - How to search memory
3. `docs/API_SESSIONS.md` - API reference
4. `docs/PHASE_2_COMPLETION_REPORT.md` - What was delivered

**Deliverables:**
- [x] Integration test suite
- [x] Complete documentation
- [x] Phase 2 completion report

---

## Success Criteria

### Functional Requirements

- [x] Sessions can be created, tracked, and ended
- [x] Session events logged automatically
- [x] AI-generated session summaries
- [x] Last session retrieval for context resumption
- [x] Temporal queries ("last 7 days")
- [x] Semantic search across sessions, tasks, projects
- [x] Unified memory search API
- [x] MCP tools for all session operations
- [x] Frontend UI for session browsing

### Performance Requirements

- Session creation: < 100ms
- Event logging: < 50ms
- Session summary generation: < 5 seconds
- Semantic search: < 500ms
- Memory search (all layers): < 1 second

### Quality Requirements

- 90%+ test coverage for session services
- All API endpoints documented
- All MCP tools tested
- Frontend components responsive
- No breaking changes to existing APIs

---

## Risk Mitigation

### Risk: Embedding Generation Cost

**Mitigation:**
- Use `text-embedding-3-small` (cheaper model)
- Batch embedding generation
- Cache embeddings, only regenerate on significant changes
- Implement rate limiting

### Risk: Database Performance (pgvector)

**Mitigation:**
- Use IVFFlat indexes for fast approximate search
- Limit search results (max 100)
- Implement pagination
- Monitor query performance

### Risk: Session Storage Growth

**Mitigation:**
- Archive sessions older than 30 days
- Compress event data
- Implement retention policies
- Monitor database size

### Risk: MCP Tool Compatibility

**Mitigation:**
- Keep HTTP API as primary interface
- MCP tools as convenience layer
- Document HTTP API usage
- Test both MCP and HTTP paths

---

## Phase 2 Deliverables Checklist

### Database Layer
- [ ] `archon_sessions` table created
- [ ] `archon_session_events` table created
- [ ] Embeddings added to existing tables
- [ ] Indexes created for performance
- [ ] Migration tested

### Backend Services
- [ ] `SessionService` implemented
- [ ] `MemorySearchService` implemented
- [ ] `EmbeddingService` implemented
- [ ] Session summarization with PydanticAI
- [ ] Background embedding generation job

### API Layer
- [ ] 8 REST endpoints for sessions
- [ ] 6 MCP tools for sessions
- [ ] 1 unified memory search endpoint
- [ ] All endpoints tested

### Frontend
- [ ] Session list view
- [ ] Session detail view
- [ ] Memory search component
- [ ] TanStack Query hooks
- [ ] Component tests

### Documentation
- [ ] Session system guide
- [ ] Memory search guide
- [ ] API reference
- [ ] Phase 2 completion report

### Testing
- [ ] Unit tests (90%+ coverage)
- [ ] Integration tests
- [ ] MCP tool tests
- [ ] Frontend component tests
- [ ] Performance tests

---

## Post-Phase 2 State

**Memory System Completion: 90%** (up from 75%)

**Memory Layer Coverage:**
- Working Memory: 90% → 92% (+2%)
- Short-Term Memory: 40% → 95% (+55%)
- Long-Term Memory: 95% → 97% (+2%)

**New Capabilities:**
- ✅ Session tracking and management
- ✅ Temporal queries across all memory
- ✅ Semantic search on tasks, projects, sessions
- ✅ AI-generated session summaries
- ✅ Context resumption from last session
- ✅ Unified memory search API

**Remaining Gaps (Phase 3-4):**
- Pattern learning system (8%)
- Advanced multi-agent coordination (2%)

---

## Phase 3 Preview (Week 3)

With Phase 2 complete, Week 3 will focus on:

1. **Pattern Learning System**
   - Pattern extraction from sessions
   - Success/failure tracking
   - Bayesian confidence scoring
   - Pattern recommendations

2. **MeshOS Taxonomy Integration**
   - Classify sessions by type
   - Knowledge/activity/decision/media categories
   - Improved pattern recognition

3. **Advanced Analytics**
   - Success rate trends
   - Agent performance metrics
   - Memory usage analytics

---

**Document Created By:** Claude (Archon Agent)
**Based On:** Memory Layer Mapping Analysis (Task 6)
**Project:** Shared Memory System Implementation
**Next:** Begin Phase 2 Implementation or Complete Week 1 Tasks 7-8
