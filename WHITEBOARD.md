# Archon Whiteboard System

Real-time visualization of multi-agent activity across the Archon platform.

## Overview

The Whiteboard is a live dashboard that displays:
- **Active Agent Sessions** - Currently running AI agents (Claude, Gemini, GPT-4)
- **Active Tasks** - Tasks with status "doing"
- **Recent Events** - Real-time event timeline (task/session lifecycle events)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Docker Logs                              │
│  (archon-server, archon-mcp, archon-ui containers)              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Enhanced Log Collector                              │
│         (archon_log_collector_enhanced.py)                       │
│                                                                   │
│  • Monitors Docker container logs                                │
│  • EventDetector with 18+ regex patterns                         │
│  • Publishes to Redis channels                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Redis Pub/Sub                                 │
│                                                                   │
│  Channels:                                                        │
│  • events:task - Task lifecycle events                           │
│  • events:session - Session lifecycle events                     │
│  • events:system - System events                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              EventListenerService                                │
│         (python/src/server/services/)                            │
│                                                                   │
│  • Subscribes to Redis channels                                  │
│  • Processes events in real-time                                 │
│  • Updates whiteboard via WhiteboardService                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              WhiteboardService                                   │
│         (python/src/server/services/)                            │
│                                                                   │
│  • Manages whiteboard document in Supabase                       │
│  • CRUD operations for sessions/tasks/events                     │
│  • Stored in archon_project_documents table                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Whiteboard API                                      │
│         (python/src/server/api_routes/whiteboard_api.py)         │
│                                                                   │
│  GET /api/whiteboard - Full whiteboard data                      │
│  GET /api/whiteboard/active-sessions                             │
│  GET /api/whiteboard/active-tasks                                │
│  GET /api/whiteboard/recent-events?limit=20                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Frontend WhiteboardView                             │
│         (archon-ui-main/src/features/projects/)                  │
│                                                                   │
│  • TanStack Query with 5-second polling                          │
│  • Three-column layout (sessions, tasks, events)                 │
│  • Manual refresh button                                         │
│  • Tron-inspired glassmorphism design                            │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### Backend Services

**1. Enhanced Log Collector** (`llm-streamer/archon_log_collector_enhanced.py`)
- Monitors Docker container logs in real-time
- Uses EventDetector for pattern matching
- Publishes structured events to Redis
- Statistics tracking (logs published, events detected)

**2. EventDetector** (`llm-streamer/event_detector.py`)
- 18+ regex patterns for event detection
- Categories: task, session, whiteboard, service, backend, error, warning, crawl, API
- Smart noise filtering (filters API requests, minor warnings)
- Structured event generation with timestamps

**3. EventListenerService** (`python/src/server/services/event_listener_service.py`)
- Background async service
- Subscribes to Redis channels (events:task, events:session)
- Processes events and updates whiteboard
- Integrated with FastAPI lifespan

**4. WhiteboardService** (`python/src/server/services/whiteboard_service.py`)
- Manages whiteboard document (ID: 8aeb549b-4cd1-4ff8-adda-87b0afbca9da)
- CRUD operations for sessions, tasks, events
- Stored in Supabase archon_project_documents table
- Content stored as JSONB with active_sessions, active_tasks, recent_events arrays

**5. Whiteboard API** (`python/src/server/api_routes/whiteboard_api.py`)
- RESTful endpoints for whiteboard data
- ETag caching support
- Error handling and logging

### Frontend Components

**1. WhiteboardView** (`archon-ui-main/src/features/projects/components/WhiteboardView.tsx`)
- Main component for whiteboard display
- Three-column grid layout
- SessionCard, TaskCard, EventCard sub-components
- Refresh button with loading state
- Relative timestamps ("Xs ago", "Xm ago")

**2. TanStack Query Hooks** (`archon-ui-main/src/features/projects/hooks/useWhiteboardQueries.ts`)
- `useActiveSessions()` - Polls every 5 seconds
- `useActiveTasks()` - Polls every 5 seconds
- `useRecentEvents(limit)` - Polls every 5 seconds
- Smart cache management with STALE_TIMES.frequent

**3. Types** (`archon-ui-main/src/features/projects/types/whiteboard.ts`)
- WhiteboardSession, WhiteboardTask, WhiteboardEvent
- Response types matching backend API

## Event Types

### Task Events
- `task.created` - New task created
- `task.status_changed` - Task status updated (todo → doing → review → done)
- `task.assigned` - Task assignee changed

### Session Events
- `session.started` - Agent session started
- `session.ended` - Agent session ended

### System Events
- `whiteboard.task_added` - Task added to whiteboard
- `whiteboard.task_updated` - Task updated on whiteboard
- `whiteboard.session_added` - Session added to whiteboard
- `whiteboard.session_removed` - Session removed from whiteboard
- `service.started` - Service started
- `service.stopped` - Service stopped
- `backend.started` - Backend started
- `backend.shutdown` - Backend shutdown
- `error.occurred` - Error detected in logs
- `warning.occurred` - Critical warning detected
- `crawl.started` - Web crawl started
- `crawl.completed` - Web crawl completed

## Usage

### Viewing the Whiteboard

1. Navigate to: http://localhost:3737
2. Select "Archon Control Plane" project
3. Click "Docs" tab
4. Select "Inter-Agent Live Stream Feed" document

The whiteboard will display:
- Active sessions with animated pulse indicators
- Active tasks (status: doing) with assignee badges
- Recent events in scrollable timeline

### Creating Test Data

**Populate with sample data:**
```bash
docker exec llm-streamer-producer python /app/populate_whiteboard.py
```

This creates:
- 3 test sessions (Claude, Gemini, GPT-4)
- 4 test tasks with various assignees

**Test session lifecycle:**
```bash
docker exec llm-streamer-producer python /app/test_session_lifecycle.py
```

**Create task via API:**
```bash
curl -X POST http://localhost:8181/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Task",
    "status": "doing",
    "assignee": "claude",
    "project_id": "6cc3ca3f-ad32-4cbf-98b3-975abbbddeee"
  }'
```

### Monitoring

**Check EventDetector logs:**
```bash
docker compose logs llm-streamer-collector --tail 50
```

**Check EventListenerService logs:**
```bash
docker compose logs archon-server | grep "Event listener"
```

**Check Redis channels:**
```bash
docker exec llm-streamer-redis redis-cli
> SUBSCRIBE events:task events:session
```

**API endpoints:**
```bash
# Get full whiteboard
curl http://localhost:8181/api/whiteboard | jq '.'

# Get active sessions
curl http://localhost:8181/api/whiteboard/active-sessions | jq '.'

# Get active tasks
curl http://localhost:8181/api/whiteboard/active-tasks | jq '.'

# Get recent events
curl http://localhost:8181/api/whiteboard/recent-events?limit=20 | jq '.'
```

## Configuration

### Environment Variables

**Redis URL:**
```env
REDIS_URL=redis://llm-streamer-redis:6379
```

**Monitored containers** (llm-streamer/archon_log_collector_enhanced.py):
```python
MONITORED_CONTAINERS = ["archon-server", "archon-mcp", "archon-ui"]
```

**Polling interval** (frontend):
```typescript
// archon-ui-main/src/features/projects/hooks/useWhiteboardQueries.ts
refetchInterval: 5000  // 5 seconds
```

**Whiteboard document ID:**
```typescript
// archon-ui-main/src/features/projects/views/ProjectsView.tsx
const WHITEBOARD_DOC_ID = "8aeb549b-4cd1-4ff8-adda-87b0afbca9da";
```

## Performance

**Request Deduplication:**
- TanStack Query deduplicates simultaneous requests
- ETag caching reduces bandwidth by ~70%

**Smart Polling:**
- 5-second intervals for real-time updates
- Visibility-aware (pauses when tab hidden)

**Event Processing:**
- Async processing via EventListenerService
- Non-blocking Redis pub/sub
- Batched whiteboard updates

## Troubleshooting

### Whiteboard not updating

**Check EventListenerService status:**
```bash
docker compose logs archon-server | grep "Event listener service"
# Should see: "✅ Event listener service started"
```

**Check Redis connectivity:**
```bash
docker compose logs archon-server | grep "REDIS_URL"
# Should show: redis://llm-streamer-redis:6379
```

**Restart services:**
```bash
docker compose restart archon-server llm-streamer-collector
```

### No events appearing

**Check EventDetector patterns:**
```bash
cd llm-streamer
python test_event_detector.py
# Should show 19/19 tests passed
```

**Check log collector:**
```bash
docker compose logs llm-streamer-collector --tail 100
# Should see "Event detected" messages
```

### Frontend import error

If you see `does not provide an export named 'default'`:
- Ensure whiteboardService.ts uses: `import { callAPIWithETag } from "@/features/shared/api/apiClient"`
- Not: `import apiClient from ...`

## Development

### Adding new event patterns

1. Edit `llm-streamer/event_detector.py`
2. Add pattern to `_build_patterns()` method
3. Add test case to `llm-streamer/test_event_detector.py`
4. Run tests: `python test_event_detector.py`
5. Restart collector: `docker compose restart llm-streamer-collector`

### Extending the frontend

1. Add new fields to types in `archon-ui-main/src/features/projects/types/whiteboard.ts`
2. Update WhiteboardView component
3. HMR will auto-reload changes

## Testing

**Run EventDetector tests:**
```bash
cd llm-streamer
python test_event_detector.py
```

**Test complete pipeline:**
```bash
# 1. Create task
curl -X POST http://localhost:8181/api/tasks -H "Content-Type: application/json" \
  -d '{"title":"Test","status":"doing","assignee":"claude","project_id":"6cc3ca3f-ad32-4cbf-98b3-975abbbddeee"}'

# 2. Check it appears on whiteboard
curl http://localhost:8181/api/whiteboard/active-tasks | jq '.active_tasks[] | select(.title == "Test")'

# 3. View in browser
open http://localhost:3737/projects/6cc3ca3f-ad32-4cbf-98b3-975abbbddeee/docs/8aeb549b-4cd1-4ff8-adda-87b0afbca9da
```

## Files Modified/Created

### Phase 1: Event Foundation
- `python/src/server/utils/event_publisher.py` (NEW)
- `python/src/server/services/projects/task_service.py` (MODIFIED)
- `python/src/server/api_routes/sessions_api.py` (MODIFIED)
- `python/pyproject.toml` (MODIFIED - added redis dependency)
- `docker-compose.yml` (MODIFIED - added REDIS_URL)

### Phase 2: Whiteboard Backend
- `python/src/server/services/whiteboard_service.py` (NEW)
- `python/src/server/services/event_listener_service.py` (NEW)
- `python/src/server/api_routes/whiteboard_api.py` (NEW)
- `python/src/server/main.py` (MODIFIED - lifespan integration)

### Phase 3: Enhanced Event Detection
- `llm-streamer/event_detector.py` (NEW)
- `llm-streamer/archon_log_collector_enhanced.py` (NEW)
- `llm-streamer/test_event_detector.py` (NEW)
- `docker-compose.yml` (MODIFIED - uses enhanced collector)

### Phase 4: Frontend Whiteboard UI
- `archon-ui-main/src/features/projects/types/whiteboard.ts` (NEW)
- `archon-ui-main/src/features/projects/services/whiteboardService.ts` (NEW)
- `archon-ui-main/src/features/projects/hooks/useWhiteboardQueries.ts` (NEW)
- `archon-ui-main/src/features/projects/components/WhiteboardView.tsx` (NEW)
- `archon-ui-main/src/features/projects/views/ProjectsView.tsx` (MODIFIED)

### Phase 5: Testing & Utilities
- `llm-streamer/populate_whiteboard.py` (NEW)
- `llm-streamer/test_session_lifecycle.py` (NEW)

## Future Enhancements

- [ ] WebSocket support for truly real-time updates (no polling)
- [ ] Event filtering/search in frontend
- [ ] Agent activity timeline visualization
- [ ] Task assignment via whiteboard UI
- [ ] Session management (pause/resume/end)
- [ ] Event playback and history
- [ ] Metrics dashboard (events per minute, active agents, etc.)
- [ ] Alert system for critical events
- [ ] Export whiteboard snapshot
- [ ] Multi-project whiteboard view

## License

Part of the Archon project.
