# Archon Project Manifest

**Last Updated:** 2026-02-17
**Project Status:** Phase 2 - 75% Complete
**Version:** Beta

---

## Quick Reference

| Component | Status | Port | Documentation |
|-----------|--------|------|---------------|
| Archon Server | ✅ Running | 8181 | `python/src/server/` |
| Archon MCP Server | ✅ Running | 8051 | `python/src/mcp_server/` |
| Archon UI | ✅ Running | 3737 | `archon-ui-main/` |
| Archon Agents | ✅ Running | 8052 | `python/src/agents/` |
| Agent Work Orders | ⚠️ Optional | 8053 | `python/src/agent_work_orders/` |
| Database | ✅ Connected | - | Supabase PostgreSQL + pgvector |

---

## System Architecture

### Tech Stack
- **Frontend**: React 18, TypeScript 5, TanStack Query v5, Tailwind CSS, Vite
- **Backend**: Python 3.12, FastAPI, Supabase, PydanticAI
- **Infrastructure**: Docker, PostgreSQL + pgvector
- **MCP**: Model Context Protocol server for AI IDE integration

### Core Capabilities
1. **Knowledge Management** - RAG, web crawling, document processing
2. **Project & Task Management** - Hierarchical task tracking
3. **Session Memory** (Phase 2) - Agent work session tracking
4. **MCP Integration** - Tools for Claude Code, Cursor, Windsurf
5. **AI Agents** - Document processing, code analysis

---

## Directory Structure

```
Archon/
├── python/src/                     # Backend Python code
│   ├── server/                     # Main FastAPI application
│   │   ├── api_routes/             # REST API endpoints (12 files)
│   │   ├── services/               # Business logic layer
│   │   ├── models/                 # Data models
│   │   ├── config/                 # Configuration
│   │   ├── middleware/             # Request processing
│   │   └── utils/                  # Shared utilities
│   ├── mcp_server/                 # MCP server (port 8051)
│   │   └── features/               # MCP tool implementations
│   │       ├── tasks/              # Task management tools
│   │       ├── sessions/           # Session management tools (Phase 2)
│   │       ├── projects/           # Project management tools
│   │       ├── rag/                # Knowledge search tools
│   │       ├── documents/          # Document tools
│   │       └── patterns/           # Pattern tools
│   ├── agents/                     # AI agents (port 8052)
│   └── agent_work_orders/          # Work order execution (port 8053)
│
├── archon-ui-main/src/             # Frontend React code
│   ├── features/                   # Vertical slice architecture
│   │   ├── knowledge/              # Knowledge base feature
│   │   ├── projects/               # Project management
│   │   │   ├── tasks/              # Task sub-feature
│   │   │   └── documents/          # Document sub-feature
│   │   ├── sessions/               # Session management (Phase 2)
│   │   ├── progress/               # Operation tracking
│   │   ├── mcp/                    # MCP integration
│   │   ├── shared/                 # Cross-feature utilities
│   │   └── ui/                     # UI components & hooks
│   ├── pages/                      # Route components
│   └── components/                 # Legacy components (migrating)
│
├── migration/                      # Database migrations
│   ├── complete_setup.sql          # Initial schema
│   ├── 002_session_memory.sql      # Phase 2: Session tables (✅ Run)
│   ├── 003_semantic_search_functions.sql  # Phase 2: Search functions (⚠️ Pending)
│   ├── 003_unified_memory_search.sql      # Phase 2: Unified search (⚠️ Pending)
│   └── 004_pattern_learning.sql    # Phase 3: Pattern tables (⚠️ Pending)
│
├── docs/                           # Project documentation
│   ├── PHASE_2_ACTUAL_STATUS.md    # Current implementation status
│   ├── MCP_TOOLS_INVENTORY.md      # MCP tools catalog
│   ├── NEXT_ACTIONS_PHASE_2.md     # Implementation roadmap
│   └── [20+ other docs]
│
├── PRPs/ai_docs/                   # AI-focused architecture docs
│   ├── ARCHITECTURE.md             # System overview
│   ├── DATA_FETCHING_ARCHITECTURE.md  # TanStack Query patterns
│   ├── API_NAMING_CONVENTIONS.md   # API standards
│   └── [7 other docs]
│
├── llm-streamer/                   # LLM event streaming (optional)
├── .env                            # Environment configuration
├── docker-compose.yml              # Service orchestration
└── README.md                       # Project overview
```

---

## Core Modules Status

### 1. Knowledge Management
**Status**: ✅ Production Ready
**Backend**: `python/src/server/services/knowledge_service.py`
**Frontend**: `archon-ui-main/src/features/knowledge/`
**API**: `/api/knowledge/*`
**MCP Tools**: `rag_search_knowledge_base`, `rag_search_code_examples`

**Features**:
- Web crawling with rate limiting
- Document upload (PDF, MD, TXT)
- Vector embeddings (OpenAI, Google, Ollama)
- RAG search with chunking strategies
- Code example extraction

### 2. Project Management
**Status**: ✅ Production Ready
**Backend**: `python/src/server/services/project_*_service.py`
**Frontend**: `archon-ui-main/src/features/projects/`
**API**: `/api/projects/*`
**MCP Tools**: `find_projects`, `manage_project`

**Features**:
- Hierarchical project organization
- Task tracking (todo, doing, review, done)
- Document versioning
- Source linking (technical/business)
- Feature tagging

### 3. Session Management (Phase 2)
**Status**: ⚠️ 75% Complete (Backend Done, Frontend Pending)
**Backend**: `python/src/server/services/session_service.py` ✅
**Frontend**: `archon-ui-main/src/features/sessions/` ❌
**API**: `/api/sessions/*` (12 endpoints) ✅
**MCP Tools**: `find_sessions`, `manage_session`, `log_session_event` ✅

**Features**:
- Agent work session tracking
- Event logging with embeddings
- Semantic search across sessions
- AI-powered summarization (PydanticAI)
- Context retrieval for resumption

**Blockers**:
- Migration 003 pending (semantic search functions)
- Frontend integration 0% complete

### 4. MCP Server
**Status**: ✅ Production Ready
**Location**: `python/src/mcp_server/`
**Port**: 8051
**Protocol**: Server-Sent Events (SSE)

**Tool Categories**:
- Task Management: 4 tools (consolidated)
- Session Management: 5 tools (Phase 2)
- Project Management: 2 tools
- Knowledge/RAG: 5 tools
- Document Management: 2 tools

**Integration**: Claude Code, Cursor, Windsurf

### 5. AI Agents
**Status**: ✅ Production Ready
**Location**: `python/src/agents/`
**Port**: 8052
**Framework**: PydanticAI

**Capabilities**:
- Document processing
- Code analysis
- Project generation
- Session summarization (Phase 2)

---

## Database Schema

### Tables (Supabase PostgreSQL + pgvector)

| Table | Purpose | Embeddings | Phase |
|-------|---------|------------|-------|
| `sources` | Knowledge sources | ❌ | 1 |
| `documents` | Document chunks | ✅ vector(1536) | 1 |
| `code_examples` | Code snippets | ❌ | 1 |
| `archon_projects` | Projects | ✅ vector(1536) | 1 |
| `archon_tasks` | Tasks | ✅ vector(1536) | 1 |
| `archon_document_versions` | Version history | ❌ | 1 |
| `archon_sessions` | Agent sessions | ✅ vector(1536) | 2 |
| `archon_session_events` | Session events | ✅ vector(1536) | 2 |
| `archon_patterns` | Learned patterns | ✅ vector(1536) | 3 (pending) |

### Indexes
- **Vector Indexes**: IVFFlat on all embedding columns
- **Temporal Indexes**: On created_at, updated_at, started_at
- **Foreign Keys**: Proper cascading deletes

### Functions
- `get_recent_sessions(agent, days, limit)` ✅
- `get_last_session(agent)` ✅
- `count_sessions_by_agent(agent, days)` ✅
- `search_sessions_semantic(embedding, limit, threshold)` ⚠️ Migration 003
- `search_all_memory_semantic(embedding, limit, threshold)` ⚠️ Migration 003

---

## API Endpoints

### Complete Endpoint Inventory

**Knowledge** (`knowledge_api.py`):
- `GET /api/knowledge/sources`
- `POST /api/knowledge/crawl`
- `POST /api/knowledge/upload`
- `POST /api/knowledge/search`
- `POST /api/knowledge/code-search`

**Projects** (`projects_api.py`):
- `GET /api/projects`
- `POST /api/projects`
- `GET /api/projects/{id}`
- `PUT /api/projects/{id}`
- `DELETE /api/projects/{id}`
- `GET /api/projects/{id}/features`
- `GET /api/projects/{id}/tasks`
- `GET /api/projects/{id}/docs`
- `POST /api/projects/{id}/versions`

**Tasks** (`projects_api.py`):
- `GET /api/tasks`
- `POST /api/tasks`
- `GET /api/tasks/{id}`
- `PUT /api/tasks/{id}`
- `DELETE /api/tasks/{id}`
- `GET /api/tasks/counts`

**Sessions** (`sessions_api.py`) - Phase 2:
- `POST /api/sessions` ✅
- `GET /api/sessions` ✅
- `GET /api/sessions/{id}` ✅
- `PUT /api/sessions/{id}` ✅
- `POST /api/sessions/{id}/end` ✅
- `POST /api/sessions/events` ✅
- `GET /api/sessions/{id}/events` ✅
- `POST /api/sessions/search` ⚠️ (needs migration 003)
- `GET /api/sessions/agents/{agent}/last` ✅
- `GET /api/sessions/agents/{agent}/recent` ✅
- `POST /api/sessions/search/all` ⚠️ (needs migration 003)
- `POST /api/sessions/{id}/summarize` ✅

**Progress** (`progress_api.py`):
- `GET /api/progress/active`
- `GET /api/progress/{id}`

**MCP** (`mcp_api.py`):
- `GET /api/mcp/status`
- `POST /api/mcp/execute`

---

## MCP Tools Inventory

### Consolidated Tool Pattern
All tools follow a consolidated pattern:
- **`find_*`** - Search, list, and get operations
- **`manage_*`** - Create, update, and delete operations

### Task Management (4 tools)
1. `archon_list_tasks` - Legacy list operation (backward compat)
2. `archon_get_task` - Legacy get operation (backward compat)
3. `find_tasks` - Consolidated search/list/get ✅
4. `manage_task` - Consolidated create/update/delete ✅

### Session Management (5 tools) - Phase 2
1. `find_sessions` - Search/list/get sessions ✅
2. `manage_session` - Create/end/update sessions ✅
3. `log_session_event` - Add events to sessions ✅
4. `search_sessions_semantic` - Semantic search ⚠️ (needs migration 003)
5. `get_agent_context` - Resume context ✅

### Project Management (2 tools)
1. `find_projects` - Search/list/get projects ✅
2. `manage_project` - Create/update/delete projects ✅

### Knowledge/RAG (5 tools)
1. `rag_search_knowledge_base` - Semantic search ✅
2. `rag_search_code_examples` - Code search ✅
3. `rag_get_available_sources` - List sources ✅
4. `rag_list_pages_for_source` - Browse structure ✅
5. `rag_read_full_page` - Retrieve full page ✅

### Document Management (2 tools)
1. `find_documents` - Search/list/get documents ✅
2. `manage_document` - Create/update/delete documents ✅

**Total**: 18 Archon tools (16 working, 2 blocked by migration 003)

---

## Frontend Architecture

### State Management
- **Server State**: TanStack Query v5 (single source of truth)
- **UI State**: React hooks & context
- **No Redux/Zustand**: Query cache handles all data

### Query Pattern Files
Each feature maintains query keys in `{feature}/hooks/use{Feature}Queries.ts`:
- `projectKeys` - Projects
- `taskKeys` - Tasks
- `sessionKeys` - Sessions (Phase 2, pending)
- `knowledgeKeys` - Knowledge
- `progressKeys` - Progress
- `mcpKeys` - MCP
- `documentKeys` - Documents

### Smart Polling
**Location**: `archon-ui-main/src/features/ui/hooks/useSmartPolling.ts`
- Visibility-aware (pauses when tab hidden)
- Variable intervals based on focus state
- Used for real-time updates without WebSockets

---

## Environment Configuration

### Required Variables
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key-here
```

### Optional Variables
```bash
# LLM Providers
OPENAI_API_KEY=
GOOGLE_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434

# Feature Flags
ENABLE_PROJECTS=true
ENABLE_AGENT_WORK_ORDERS=false

# Ports (defaults)
ARCHON_SERVER_PORT=8181
ARCHON_MCP_PORT=8051
ARCHON_UI_PORT=3737
ARCHON_AGENTS_PORT=8052
```

See `.env.example` for complete list.

---

## Development Commands

### Start Services
```bash
# Full Docker mode (recommended)
docker compose up --build -d

# Hybrid mode (backend in Docker, frontend local)
docker compose --profile backend up -d
cd archon-ui-main && npm run dev

# All local (3 terminals)
cd python && uv run python -m src.server.main
cd archon-ui-main && npm run dev
# MCP server runs in Docker or via Docker
```

### Linting & Testing
```bash
# Frontend
cd archon-ui-main
npm run lint              # ESLint (legacy)
npm run biome             # Biome (features/)
npm run test              # Vitest

# Backend
cd python
uv run ruff check         # Linter
uv run mypy src/          # Type checker
uv run pytest             # Tests
```

### Database Operations
```bash
# Run migration in Supabase SQL Editor
# Copy contents of migration/*.sql and execute

# Verify migration
# Use queries from docs/testDB.md
```

---

## Phase Status

### Phase 1: MCP Connection & Validation (Week 1)
**Status**: ✅ 75% Complete
**Date**: 2026-02-14

- ✅ MCP server validation
- ✅ Tool inventory (docs/MCP_TOOLS_INVENTORY.md)
- ✅ Tool consolidation refactor
- ✅ Memory layer mapping

### Phase 2: Session Memory & Semantic Search
**Status**: ⚠️ 75% Complete (Backend Done)
**Started**: 2026-02-14
**Target**: 90% completion

**Completed**:
- ✅ Day 1: Database schema (migration 002)
- ✅ Day 2: SessionService (15 methods)
- ✅ Day 3: API endpoints (12 endpoints)
- ✅ Day 3: MCP tools (5 tools)
- ✅ Day 5: AI summarization (PydanticAI)

**Pending**:
- ⚠️ Day 4: Semantic search (migration 003 not run)
- ❌ Day 6-7: Frontend integration (0%)
- ❌ Day 8: Testing & documentation

**Blockers**:
1. Migration 003 pending (semantic search functions)
2. Frontend not started

**Next Steps**:
1. Run migration 003 in Supabase (10 minutes)
2. Build frontend components (2-3 days)
3. Integration testing (1 day)

See `docs/PHASE_2_ACTUAL_STATUS.md` for detailed status.

### Phase 3: Pattern Learning (Future)
**Status**: ❌ Not Started
**Requires**: Migration 004 (`archon_patterns` table)

### Phase 4: Multi-Agent Coordination (Future)
**Status**: ❌ Not Started

---

## Documentation Index

### Architecture & Design
- `PRPs/ai_docs/ARCHITECTURE.md` - System architecture overview
- `PRPs/ai_docs/DATA_FETCHING_ARCHITECTURE.md` - TanStack Query patterns
- `PRPs/ai_docs/API_NAMING_CONVENTIONS.md` - API conventions
- `PRPs/ai_docs/QUERY_PATTERNS.md` - Frontend query patterns
- `PRPs/ai_docs/UI_STANDARDS.md` - UI component guidelines
- `PRPs/ai_docs/ETAG_IMPLEMENTATION.md` - Caching strategy

### Implementation Guides
- `docs/PHASE_2_ACTUAL_STATUS.md` - Current phase status (detailed)
- `docs/NEXT_ACTIONS_PHASE_2.md` - Implementation roadmap
- `docs/MCP_TOOLS_INVENTORY.md` - MCP tools catalog
- `docs/SESSION_SERVICE_GUIDE.md` - Session service documentation
- `docs/SHARED_MEMORY_PROJECT_GUIDE.md` - Memory system guide

### Database
- `docs/testDB.md` - Database verification tests
- `docs/RUN_MIGRATION_002.md` - Migration 002 guide
- `docs/RUN_MIGRATION_003.md` - Migration 003 guide

### Project Status
- `docs/WEEK_1_COMPLETION_SUMMARY.md` - Phase 1 summary
- `docs/DAY_2_COMPLETION_SUMMARY.md` - Phase 2 Day 2
- `docs/DAY_3_COMPLETION_SUMMARY.md` - Phase 2 Day 3
- `docs/DAY_4_COMPLETION_SUMMARY.md` - Phase 2 Day 4
- `docs/DAY_5_COMPLETION_SUMMARY.md` - Phase 2 Day 5

### User Documentation
- `README.md` - Quick start and overview
- `CONTRIBUTING.md` - Contribution guidelines

---

## Agile Status

### Current Sprint: Phase 2 Session Memory
**Sprint Goal**: Complete session memory backend and frontend integration
**Sprint Duration**: 8 days (2026-02-14 to 2026-02-22)
**Completion**: 75% (6 of 8 days)

### Backlog
1. ✅ Database schema (1 day) - DONE
2. ✅ SessionService implementation (1 day) - DONE
3. ✅ API endpoints (1 day) - DONE
4. ⚠️ Semantic search (0.5 days) - BLOCKED (migration 003)
5. ✅ AI summarization (0.5 days) - DONE
6. ❌ Frontend integration (2 days) - NOT STARTED
7. ❌ Testing (1 day) - NOT STARTED

### Definition of Done
- [ ] All migrations run
- [ ] All tests passing
- [ ] Frontend components implemented
- [ ] Documentation updated
- [ ] MCP tools verified in IDE
- [ ] No critical bugs

---

## Known Issues & Limitations

### Phase 2 Blockers
1. **Migration 003 not run** - Semantic search functions missing
   - Impact: `/api/sessions/search` returns 404
   - Resolution: Execute migration in Supabase SQL Editor
   - Priority: HIGH

2. **Frontend not started** - 0% complete
   - Impact: No UI for session management
   - Resolution: Build session timeline components
   - Priority: HIGH

### General Limitations
- **Beta Status**: Expect bugs and breaking changes
- **Single Tenant**: No multi-tenancy support yet
- **No WebSockets**: Uses HTTP polling (smart intervals)
- **No Offline Mode**: Requires network connection

---

## Quick Health Check

```bash
# Verify all services running
docker compose ps

# Check API health
curl http://localhost:8181/api/projects | jq '.projects | length'

# Check MCP server
curl http://localhost:8051/health

# Check UI
open http://localhost:3737
```

**Expected**: All services showing "Up" status, API returning data, UI accessible

---

## Support & Resources

- **GitHub**: https://github.com/coleam00/Archon
- **Discussions**: https://github.com/coleam00/Archon/discussions
- **Issues**: https://github.com/coleam00/Archon/issues
- **Kanban Board**: https://github.com/users/coleam00/projects/1

---

**Manifest Version**: 1.0
**Last Audit**: 2026-02-17
**Next Review**: After Phase 2 completion
