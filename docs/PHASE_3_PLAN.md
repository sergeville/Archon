# Phase 3: Frontend Integration for Shared Memory System

**Phase**: 3 - Frontend Integration
**Started**: 2026-02-18
**Status**: 🚀 IN PROGRESS

## Overview

Phase 3 integrates the completed Phase 2 backend (Shared Memory System) into the Archon frontend, providing users with a visual interface to:
- View agent work sessions
- Browse conversation history
- Search across sessions semantically
- Track agent activity and events
- Resume previous sessions with full context

## Prerequisites (Phase 2 - COMPLETE ✅)

- ✅ Database schema with vector embeddings (migrations 002, 003, 004)
- ✅ SessionService with 15 methods
- ✅ MemoryService with 5 methods
- ✅ 12 REST API endpoints
- ✅ 5 MCP tools
- ✅ Embeddings generated for 31 records
- ✅ Semantic search infrastructure

## Phase 3 Goals

### Primary Goals
1. **Sessions Dashboard** - View all agent work sessions
2. **Session Detail View** - Deep dive into session events and conversations
3. **Conversation History** - Browse and search message history
4. **Semantic Search UI** - Search across all memory layers
5. **Session Resume** - Load context from previous sessions

### Secondary Goals
6. Real-time session updates (WebSocket/polling)
7. Session analytics and statistics
8. Export session data
9. Session comparison view

## Implementation Plan

### Task 1: Feature Structure Setup (30 min)

**Directory**: `archon-ui-main/src/features/sessions/`

**Structure**:
```
sessions/
├── components/
│   ├── SessionCard.tsx
│   ├── SessionList.tsx
│   ├── SessionDetail.tsx
│   ├── ConversationThread.tsx
│   ├── EventTimeline.tsx
│   └── SearchInterface.tsx
├── hooks/
│   └── useSessionQueries.ts
├── services/
│   └── sessionService.ts
├── types/
│   └── index.ts
├── views/
│   └── SessionsView.tsx
└── index.ts
```

**Acceptance Criteria**:
- ✅ Directory structure created
- ✅ Barrel exports configured
- ✅ Feature registered in app

### Task 2: TypeScript Types (20 min)

**File**: `sessions/types/index.ts`

**Types to Define**:
```typescript
// Core entities
export interface Session {
  id: string;
  agent: string;
  project_id?: string;
  started_at: string;
  ended_at?: string;
  summary?: string;
  context: Record<string, any>;
  metadata: Record<string, any>;
  embedding?: number[];
}

export interface SessionEvent {
  id: string;
  session_id: string;
  event_type: string;
  event_data: Record<string, any>;
  created_at: string;
  metadata: Record<string, any>;
  embedding?: number[];
}

export interface Conversation {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  message: string;
  tools_used?: string[];
  type?: string;
  subtype?: string;
  created_at: string;
  metadata: Record<string, any>;
  embedding?: number[];
}

// Request types
export interface CreateSessionRequest {
  agent: string;
  project_id?: string;
  context?: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface SearchSessionsRequest {
  query: string;
  limit?: number;
  threshold?: float;
}

// Response types
export interface SessionsResponse {
  sessions: Session[];
  total: number;
}

export interface SearchResult<T> {
  results: T[];
  total: number;
}
```

**Acceptance Criteria**:
- ✅ All backend response types mirrored
- ✅ Request types defined
- ✅ Generic types for reusability
- ✅ TypeScript strict mode compliant

### Task 3: API Service Layer (45 min)

**File**: `sessions/services/sessionService.ts`

**Methods** (matching backend endpoints):
```typescript
export const sessionService = {
  // Session CRUD
  async listSessions(params?): Promise<SessionsResponse>
  async getSession(id: string): Promise<Session>
  async createSession(data: CreateSessionRequest): Promise<Session>
  async updateSession(id: string, data: UpdateSessionRequest): Promise<Session>
  async endSession(id: string, summary?: string): Promise<Session>

  // Events
  async logEvent(data: LogEventRequest): Promise<SessionEvent>
  async getSessionEvents(sessionId: string): Promise<SessionEvent[]>

  // Search
  async searchSessions(query: SearchSessionsRequest): Promise<SearchResult<Session>>
  async searchAll(query: SearchSessionsRequest): Promise<SearchResult<any>>

  // Agent-specific
  async getLastSession(agent: string): Promise<Session | null>
  async getRecentSessions(agent: string, days: number): Promise<Session[]>

  // AI
  async summarizeSession(sessionId: string): Promise<{summary: string}>
}
```

**Acceptance Criteria**:
- ✅ All 12 API endpoints wrapped
- ✅ Proper error handling
- ✅ TypeScript types enforced
- ✅ Uses shared apiClient

### Task 4: TanStack Query Hooks (60 min)

**File**: `sessions/hooks/useSessionQueries.ts`

**Query Key Factory**:
```typescript
export const sessionKeys = {
  all: ['sessions'] as const,
  lists: () => [...sessionKeys.all, 'list'] as const,
  detail: (id: string) => [...sessionKeys.all, 'detail', id] as const,
  events: (sessionId: string) => [...sessionKeys.all, sessionId, 'events'] as const,
  search: (query: string) => [...sessionKeys.all, 'search', query] as const,
  agentLast: (agent: string) => [...sessionKeys.all, 'agent', agent, 'last'] as const,
  agentRecent: (agent: string) => [...sessionKeys.all, 'agent', agent, 'recent'] as const,
}
```

**Hooks**:
```typescript
export function useSessions()
export function useSession(id: string)
export function useSessionEvents(sessionId: string)
export function useSearchSessions(query: string)
export function useAgentLastSession(agent: string)
export function useCreateSession()
export function useUpdateSession()
export function useEndSession()
export function useLogEvent()
export function useSummarizeSession()
```

**Patterns**:
- Use `STALE_TIMES` from shared config
- Implement smart polling for active sessions
- Optimistic updates for mutations
- Proper error states

**Acceptance Criteria**:
- ✅ Query keys follow factory pattern
- ✅ All CRUD hooks implemented
- ✅ Search hooks with debouncing
- ✅ Optimistic updates for mutations
- ✅ Smart polling configured

### Task 5: Sessions List View (90 min)

**Component**: `SessionCard.tsx`

**Features**:
- Agent badge with color coding
- Session duration display
- Status indicator (active/ended)
- Summary preview
- Click to view details

**Component**: `SessionList.tsx`

**Features**:
- Grid/list toggle
- Filter by agent
- Filter by status (active/ended)
- Sort by date (newest/oldest)
- Search sessions
- Empty state
- Loading states
- Error states

**Component**: `SessionsView.tsx`

**Layout**:
```
┌─────────────────────────────────────┐
│  Sessions                    [+ New]│
│  ┌───────────────────────────────┐  │
│  │ 🔍 Search  [Agent▾] [Status▾]│  │
│  └───────────────────────────────┘  │
│  ┌───────┐ ┌───────┐ ┌───────┐    │
│  │Session│ │Session│ │Session│    │
│  │ Card  │ │ Card  │ │ Card  │    │
│  └───────┘ └───────┘ └───────┘    │
└─────────────────────────────────────┘
```

**Acceptance Criteria**:
- ✅ Responsive grid layout
- ✅ Real-time updates (polling)
- ✅ Filters working
- ✅ Search functional
- ✅ Loading/error states
- ✅ Empty state with CTA

### Task 6: Session Detail View (90 min)

**Component**: `SessionDetail.tsx`

**Sections**:
1. **Header** - Agent, status, duration, actions
2. **Summary** - AI-generated or manual summary
3. **Context** - Session context data
4. **Events** - Timeline of session events
5. **Conversations** - Message thread
6. **Metadata** - Additional info

**Component**: `EventTimeline.tsx`

**Features**:
- Chronological event list
- Event type icons
- Expandable event data
- Timestamps (relative and absolute)

**Component**: `ConversationThread.tsx`

**Features**:
- Chat-like message display
- User/assistant/system differentiation
- Code block rendering
- Tool usage badges
- Copy message functionality

**Acceptance Criteria**:
- ✅ All session data displayed
- ✅ Events in chronological order
- ✅ Conversations properly formatted
- ✅ Actions working (end, summarize)
- ✅ Responsive design

### Task 7: Semantic Search UI (60 min)

**Component**: `SearchInterface.tsx`

**Features**:
- Search input with debouncing
- Similarity threshold slider
- Result type filter (sessions/events/conversations)
- Results with relevance scores
- Click to navigate to source

**Layout**:
```
┌─────────────────────────────────────┐
│  🔍 Search across all memory...     │
│  Similarity: [====○-----] 0.7       │
│  [Sessions] [Events] [Conversations]│
│                                      │
│  Results:                            │
│  ┌──────────────────────────────┐   │
│  │ 💬 "database migration"      │   │
│  │ Session: abc-123  │  0.85     │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
```

**Acceptance Criteria**:
- ✅ Search across all memory layers
- ✅ Results ranked by relevance
- ✅ Threshold filtering
- ✅ Type filtering
- ✅ Navigate to source

### Task 8: Routing and Navigation (30 min)

**Routes to Add**:
- `/sessions` - Sessions list
- `/sessions/:id` - Session detail
- `/sessions/search` - Semantic search

**Navigation**:
- Add Sessions link to sidebar
- Breadcrumbs on detail pages
- Back navigation

**Acceptance Criteria**:
- ✅ Routes registered
- ✅ Navigation working
- ✅ Deep linking functional
- ✅ Breadcrumbs accurate

### Task 9: Testing and Polish (60 min)

**Testing**:
- Component unit tests
- Hook tests with mock data
- Service layer tests
- E2E user flows

**Polish**:
- Loading skeletons
- Transitions and animations
- Error boundaries
- Accessibility (ARIA labels, keyboard nav)
- Mobile responsive

**Acceptance Criteria**:
- ✅ Core components tested
- ✅ Hooks tested
- ✅ No TypeScript errors
- ✅ Accessibility audit passed
- ✅ Mobile tested

## API Endpoints Reference

### Session Management
- `GET /api/sessions` - List all sessions
- `POST /api/sessions` - Create new session
- `GET /api/sessions/{id}` - Get session details
- `PUT /api/sessions/{id}` - Update session
- `POST /api/sessions/{id}/end` - End session

### Events
- `POST /api/sessions/events` - Log event
- `GET /api/sessions/{id}/events` - Get session events

### Search
- `POST /api/sessions/search` - Search sessions
- `POST /api/sessions/search/all` - Unified memory search

### Agent-Specific
- `GET /api/sessions/agents/{agent}/last` - Last session for agent
- `GET /api/sessions/agents/{agent}/recent` - Recent sessions

### AI Features
- `POST /api/sessions/{id}/summarize` - Generate AI summary

## Design System Integration

### Colors (Tron Theme)
- Active sessions: Cyan glow
- Ended sessions: Gray/muted
- Agent badges: Color-coded by agent type
- Search results: Highlighted matches

### Components (Radix UI)
- Cards: `src/features/ui/primitives/card`
- Buttons: `src/features/ui/primitives/button`
- Dialogs: `src/features/ui/primitives/dialog`
- Badges: `src/features/ui/primitives/badge`

### Patterns
- Follow existing project/task patterns
- Use shared layouts
- Maintain consistency with design system

## Performance Considerations

### Optimization Strategies
1. **Pagination** - Load sessions in batches
2. **Virtual Scrolling** - For long conversation threads
3. **Smart Polling** - Only for active sessions
4. **Debounced Search** - 300ms delay
5. **Memoization** - Expensive computations
6. **Lazy Loading** - Code splitting for search

### Caching Strategy
- **Instant**: Active session data
- **Normal** (30s): Session lists
- **Rare** (5min): Ended sessions
- **Static**: Agent types

## Success Metrics

### Functionality
- ✅ All 12 API endpoints integrated
- ✅ CRUD operations working
- ✅ Search functionality operational
- ✅ Real-time updates active

### Performance
- ✅ Page load < 1s
- ✅ Search results < 500ms
- ✅ No layout shift (CLS < 0.1)
- ✅ Mobile responsive (320px+)

### Quality
- ✅ TypeScript strict mode passing
- ✅ No console errors
- ✅ Accessibility score > 90
- ✅ All links functional

## Timeline

**Total Estimated Time**: ~7 hours

**Breakdown**:
- Task 1: Feature setup (30 min)
- Task 2: Types (20 min)
- Task 3: Service layer (45 min)
- Task 4: Query hooks (60 min)
- Task 5: List view (90 min)
- Task 6: Detail view (90 min)
- Task 7: Search UI (60 min)
- Task 8: Routing (30 min)
- Task 9: Testing (60 min)

**Phases**:
- **Phase 3.1** (2-3 hours): Core infrastructure (Tasks 1-4)
- **Phase 3.2** (2-3 hours): UI components (Tasks 5-6)
- **Phase 3.3** (1-2 hours): Search and polish (Tasks 7-9)

## Dependencies

### Required
- ✅ Phase 2 backend complete
- ✅ API server running
- ✅ Database with embeddings

### Optional
- ⚠️ Valid embedding provider for runtime search
- WebSocket server for real-time updates (future)

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Embedding API expired | Search won't work | Configure Ollama for runtime |
| Large session data | Slow rendering | Virtual scrolling, pagination |
| Complex UI state | Bugs | TanStack Query handles it |
| Mobile layout | Poor UX | Mobile-first design |

## Future Enhancements (Phase 4+)

1. **WebSocket Integration** - Real-time session updates
2. **Session Comparison** - Side-by-side view
3. **Export Functionality** - Download session data
4. **Analytics Dashboard** - Session statistics
5. **Session Templates** - Pre-configured contexts
6. **Collaboration** - Share sessions between users
7. **Session Replay** - Step through session timeline

## Related Documentation

- **Phase 2 Summary**: `docs/PHASE_2_COMPLETE_SUMMARY.md`
- **Backend API**: `python/src/server/api_routes/sessions_api.py`
- **SessionService**: `python/src/server/services/session_service.py`
- **MemoryService**: `python/src/server/services/memory_service.py`
- **Architecture**: `PRPs/ai_docs/ARCHITECTURE.md`
- **Query Patterns**: `PRPs/ai_docs/QUERY_PATTERNS.md`
- **Data Fetching**: `PRPs/ai_docs/DATA_FETCHING_ARCHITECTURE.md`

---

**Created By**: Claude (Archon Agent)
**Date**: 2026-02-18
**Status**: 🚀 Ready to implement
**Next Step**: Task 1 - Feature Structure Setup
