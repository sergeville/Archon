# Whiteboard System - Deployment Guide

Quick reference for deploying and verifying the Archon whiteboard system.

## Prerequisites

- Docker and Docker Compose installed
- Archon services running (archon-server, archon-mcp, archon-ui)
- Redis container (llm-streamer-redis)

## Services Overview

The whiteboard system consists of these services:

```bash
docker compose ps
```

**Required services:**
- `archon-server` - Backend API (port 8181)
- `archon-mcp` - MCP server (port 8051)
- `archon-frontend` - Frontend UI (port 3737)
- `llm-streamer-redis` - Redis pub/sub (port 6379)
- `llm-streamer-collector` - Enhanced log collector

## Deployment Steps

### 1. Start All Services

```bash
# From Archon root directory
docker compose up -d
```

### 2. Verify Services

**Check all services are healthy:**
```bash
docker compose ps
```

**Expected status:**
- archon-server: Up (healthy)
- archon-mcp: Up (healthy)
- archon-frontend: Up (healthy)
- llm-streamer-redis: Up (healthy)
- llm-streamer-collector: Up

### 3. Verify EventListenerService

**Check it started:**
```bash
docker compose logs archon-server | grep "Event listener service"
```

**Expected output:**
```
✅ Subscribed to Redis channels: events:task, events:session
Event listener service started successfully
```

### 4. Verify Enhanced Collector

**Check it's monitoring:**
```bash
docker compose logs llm-streamer-collector --tail 20
```

**Expected output:**
```
🔍 Archon Log Collector (Enhanced) started
📡 Publishing to Redis: redis://llm-streamer-redis:6379
👀 Monitoring containers: archon-server, archon-mcp, archon-ui
📊 Event detection enabled

[timestamp] [collector] Connected to archon-server
[timestamp] [collector] Connected to archon-mcp
[timestamp] [collector] Connected to archon-ui
```

### 5. Verify Whiteboard API

**Test API endpoints:**
```bash
# Full whiteboard
curl -s http://localhost:8181/api/whiteboard | jq '.whiteboard.id'
# Should return: "8aeb549b-4cd1-4ff8-adda-87b0afbca9da"

# Active sessions
curl -s http://localhost:8181/api/whiteboard/active-sessions | jq '.count'

# Active tasks
curl -s http://localhost:8181/api/whiteboard/active-tasks | jq '.count'

# Recent events
curl -s http://localhost:8181/api/whiteboard/recent-events | jq '.count'
```

### 6. Access Frontend

**Open in browser:**
```
http://localhost:3737/projects/6cc3ca3f-ad32-4cbf-98b3-975abbbddeee/docs/8aeb549b-4cd1-4ff8-adda-87b0afbca9da
```

Or navigate manually:
1. Go to http://localhost:3737
2. Select "Archon Control Plane" project
3. Click "Docs" tab
4. Click "Inter-Agent Live Stream Feed"

## Testing the System

### Create Test Data

**Populate whiteboard:**
```bash
docker exec llm-streamer-producer python /app/populate_whiteboard.py
```

**Expected output:**
```
======================================================================
Populating Whiteboard with Test Data
======================================================================
✅ Connected to Redis

📡 Publishing session events...
  ✅ Published: Claude Sonnet 4.5 (session: session-claude-001)
  ✅ Published: Gemini Pro (session: session-gemini-001)
  ✅ Published: GPT-4 Turbo (session: session-gpt4-001)

📋 Publishing task events...
  ✅ Published: Implement Whiteboard Real-Time Updates
  ✅ Published: Optimize Event Detection Patterns
  ✅ Published: Design Shared Memory Architecture
  ✅ Published: Update API Documentation

✅ All events published successfully!
```

### Verify Data Appears

**Check API:**
```bash
curl -s http://localhost:8181/api/whiteboard/active-sessions | jq '.active_sessions | length'
# Should return: 3

curl -s http://localhost:8181/api/whiteboard/active-tasks | jq '.active_tasks | length'
# Should be > 0
```

**Check frontend:**
- Refresh browser
- Should see 3 active sessions
- Should see multiple active tasks
- Should see recent events

### Test Event Pipeline

**Create a new task:**
```bash
curl -X POST http://localhost:8181/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Task",
    "status": "doing",
    "assignee": "claude",
    "project_id": "6cc3ca3f-ad32-4cbf-98b3-975abbbddeee"
  }'
```

**Verify it appears:**
```bash
# Check logs
docker compose logs archon-server --tail 10 | grep "Event published"
docker compose logs archon-server --tail 10 | grep "Added task"

# Check API
curl -s http://localhost:8181/api/whiteboard/active-tasks | jq '.active_tasks[] | select(.title == "Test Task")'

# Check browser - should see task appear within 5 seconds
```

### Test Session Lifecycle

**End a session:**
```bash
docker exec llm-streamer-producer python /app/test_session_lifecycle.py
```

**Expected:**
- Gemini Pro session removed from whiteboard
- Event appears in recent events
- Browser updates within 5 seconds

## Monitoring

### View Real-Time Events

**Subscribe to Redis channels:**
```bash
docker exec llm-streamer-redis redis-cli
> SUBSCRIBE events:task events:session events:system
```

**Create a task and watch it flow through:**
```bash
# In another terminal, create task
curl -X POST http://localhost:8181/api/tasks -H "Content-Type: application/json" \
  -d '{"title":"Monitor Test","status":"doing","assignee":"claude","project_id":"6cc3ca3f-ad32-4cbf-98b3-975abbbddeee"}'

# Watch Redis subscriber - should see event immediately
```

### Check Collector Statistics

```bash
docker compose logs llm-streamer-collector | grep "📈"
```

**Output:**
```
📈 Archon Log Collector Statistics
Logs published: 543
Events detected: 23
Events by type:
  task.created: 8
  task.status_changed: 7
  session.started: 5
  ...
```

### Monitor Event Processing

```bash
# Watch EventListenerService
docker compose logs archon-server -f | grep "Event listener"

# Should see:
# Added task xxx to whiteboard
# Updated task xxx on whiteboard
# Added session xxx to whiteboard
# Removed session xxx from whiteboard
```

## Troubleshooting

### Collector Not Running

**Symptom:** No events detected

**Fix:**
```bash
# Check status
docker compose ps llm-streamer-collector

# Restart
docker compose restart llm-streamer-collector

# Check logs
docker compose logs llm-streamer-collector --tail 50
```

### EventListenerService Not Started

**Symptom:** Whiteboard not updating

**Check:**
```bash
docker compose logs archon-server | grep "Event listener"
```

**Fix:**
```bash
# Verify REDIS_URL environment variable
docker exec archon-server env | grep REDIS_URL
# Should be: redis://llm-streamer-redis:6379

# Restart server
docker compose restart archon-server
```

### Frontend Not Loading Whiteboard

**Symptom:** Blank page or error

**Check browser console:**
- Look for import errors
- Look for API errors

**Fix import error:**
```bash
# Check whiteboardService.ts uses correct import
grep "import.*apiClient" archon-ui-main/src/features/projects/services/whiteboardService.ts
# Should use: import { callAPIWithETag } from ...
```

**Restart frontend:**
```bash
docker compose restart archon-frontend
```

### No Data in Whiteboard

**Symptom:** Empty sessions/tasks/events

**Create test data:**
```bash
docker exec llm-streamer-producer python /app/populate_whiteboard.py
```

**Or create real task:**
```bash
curl -X POST http://localhost:8181/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","status":"doing","assignee":"claude","project_id":"6cc3ca3f-ad32-4cbf-98b3-975abbbddeee"}'

# Update status to doing
curl -X PUT http://localhost:8181/api/tasks/{task_id} \
  -H "Content-Type: application/json" \
  -d '{"status":"doing"}'
```

## Restart All Services

If issues persist:

```bash
# Stop all
docker compose down

# Start all
docker compose up -d

# Wait for health checks
sleep 30

# Verify
docker compose ps
docker compose logs archon-server | grep "Event listener"
docker compose logs llm-streamer-collector --tail 20
```

## Health Check Endpoints

```bash
# Server health
curl http://localhost:8181/health

# MCP health
curl http://localhost:8051/health

# Frontend
curl http://localhost:3737
```

## Port Reference

- **3737** - Frontend UI
- **8181** - Backend API
- **8051** - MCP Server
- **6379** - Redis (internal only)
- **8000** - LLM Streamer Gateway (optional)

## File Locations

**Backend:**
- Event Publisher: `python/src/server/utils/event_publisher.py`
- WhiteboardService: `python/src/server/services/whiteboard_service.py`
- EventListenerService: `python/src/server/services/event_listener_service.py`
- Whiteboard API: `python/src/server/api_routes/whiteboard_api.py`

**Collector:**
- Enhanced Collector: `llm-streamer/archon_log_collector_enhanced.py`
- EventDetector: `llm-streamer/event_detector.py`
- Tests: `llm-streamer/test_event_detector.py`

**Frontend:**
- WhiteboardView: `archon-ui-main/src/features/projects/components/WhiteboardView.tsx`
- Hooks: `archon-ui-main/src/features/projects/hooks/useWhiteboardQueries.ts`
- Service: `archon-ui-main/src/features/projects/services/whiteboardService.ts`
- Types: `archon-ui-main/src/features/projects/types/whiteboard.ts`

## Quick Commands

```bash
# Restart everything
docker compose restart

# View all logs
docker compose logs -f

# Check specific service
docker compose logs archon-server -f

# Run tests
cd llm-streamer && python test_event_detector.py

# Populate test data
docker exec llm-streamer-producer python /app/populate_whiteboard.py

# Monitor Redis events
docker exec llm-streamer-redis redis-cli
> SUBSCRIBE events:task events:session events:system
```

## Next Steps

After deployment:
1. Create real tasks and sessions
2. Monitor the whiteboard for updates
3. Review event logs for insights
4. Customize event patterns as needed
5. Add more event types for your use cases
