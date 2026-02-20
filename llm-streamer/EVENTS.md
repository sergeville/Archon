# Event Detection System

Enhanced log collection with intelligent event detection for Archon whiteboard integration.

## Overview

The Event Detection System monitors Docker container logs and automatically detects structured events that update the Archon whiteboard in real-time.

## Architecture

```
Docker Logs → Enhanced Collector → EventDetector → Redis Pub/Sub → EventListenerService → Whiteboard
```

## Components

### Enhanced Log Collector
**File:** `archon_log_collector_enhanced.py`

Real-time log monitoring with dual publishing:
- **Raw logs** → `logs` channel (for UI display)
- **Structured events** → `events:*` channels (for whiteboard)

**Features:**
- Monitors multiple containers simultaneously
- Non-blocking async streams
- Automatic reconnection
- Statistics tracking

### EventDetector
**File:** `event_detector.py`

Pattern matching engine with 18+ regex patterns.

**Event Categories:**
- Task events (created, status_changed, assigned)
- Session events (started, ended)
- Whiteboard events (task_added, task_updated, session_added/removed)
- Service events (started, stopped)
- Backend events (started, shutdown)
- Error/Warning events
- Crawl events (started, completed)
- API events (filtered from events channels)

## Detected Events

### Task Events

**task.created**
```
Pattern: "Published task.created event for task ([\w-]+)"
Channel: events:task
Data: {task_id}
```

**task.status_changed**
```
Pattern: "Published task.status_changed event for task ([\w-]+)"
Channel: events:task
Data: {task_id}
```

**task.assigned**
```
Pattern: "Published task.assigned event for task ([\w-]+)"
Channel: events:task
Data: {task_id}
```

### Session Events

**session.started**
```
Pattern: "Published session.started event for session ([\w-]+)"
Channel: events:session
Data: {session_id}
```

**session.ended**
```
Pattern: "Published session.ended event for session ([\w-]+)"
Channel: events:session
Data: {session_id}
```

### Whiteboard Events

**whiteboard.task_added**
```
Pattern: "Added task ([\w-]+) to whiteboard"
Channel: events:system
Data: {task_id}
```

**whiteboard.task_updated**
```
Pattern: "Updated task ([\w-]+) on whiteboard: (\w+) → (\w+)"
Channel: events:system
Data: {task_id, old_status, new_status}
```

**whiteboard.session_added**
```
Pattern: "Added session ([\w-]+) \((\w+)\) to whiteboard"
Channel: events:system
Data: {session_id, agent}
```

**whiteboard.session_removed**
```
Pattern: "Removed session ([\w-]+) from whiteboard"
Channel: events:system
Data: {session_id}
```

### Service Events

**service.started**
```
Pattern: "([\w-]+) service started successfully"
Channel: events:system
Data: {service_name}
```

**service.stopped**
```
Pattern: "([\w-]+) service stopped"
Channel: events:system
Data: {service_name}
```

### Backend Events

**backend.started**
```
Pattern: "🎉 Archon backend started successfully!"
Channel: events:system
Data: {}
```

**backend.shutdown**
```
Pattern: "🛑 Shutting down Archon backend"
Channel: events:system
Data: {}
```

### Error/Warning Events

**error.occurred**
```
Pattern: "ERROR.*?:\s*(.+)$"
Channel: events:system
Data: {error_message}
```

**warning.occurred** (filtered)
```
Pattern: "WARNING.*?:\s*(.+)$"
Channel: events:system
Data: {warning_message}
Note: Only critical warnings published (containing "Could not start" or "Failed to")
```

### Crawl Events

**crawl.started**
```
Pattern: "Starting crawl for URL: (.+)"
Channel: events:system
Data: {url}
```

**crawl.completed**
```
Pattern: "Crawl completed for (.+)"
Channel: events:system
Data: {url}
```

### API Events (Filtered)

**api.request** (NOT published to events)
```
Pattern: "(GET|POST|PUT|DELETE|PATCH)\s+(/api/[\w/]+)"
Channel: N/A (filtered)
Data: {method, path}
Note: Too noisy, only published to 'logs' channel
```

## Event Structure

All events follow this structure:

```json
{
  "event_type": "task.created",
  "entity_type": "task",
  "entity_id": "task-123",
  "timestamp": "2026-02-16T17:00:00.000000+00:00",
  "source": "archon-server",
  "data": {
    "log_line": "Original log line...",
    "task_id": "task-123",
    "title": "Task Title",
    "status": "doing",
    "assignee": "claude"
  }
}
```

**Fields:**
- `event_type` - Event identifier (e.g., "task.created")
- `entity_type` - Entity category (task, session, service, etc.)
- `entity_id` - Unique identifier (task_id, session_id, etc.)
- `timestamp` - ISO 8601 timestamp (UTC)
- `source` - Container name (archon-server, archon-mcp, archon-ui)
- `data` - Event-specific data including original log line

## Noise Filtering

The EventDetector implements smart noise filtering:

**API Requests:**
- Detected but NOT published to `events:*` channels
- Still published to `logs` channel for UI
- Reason: Too frequent (every request)

**Warnings:**
- Only critical warnings published
- Must contain "Could not start" OR "Failed to"
- Minor warnings filtered out
- Reason: Reduce noise from routine warnings

**Pattern:** All events detected go through `should_publish_to_events()` filter.

## Testing

### Run Test Suite
```bash
cd llm-streamer
python test_event_detector.py
```

**Expected output:**
```
======================================================================
EventDetector Pattern Matching Test
======================================================================
✅ PASS: task.created
✅ PASS: task.status_changed
✅ PASS: session.started
✅ PASS: session.ended
✅ PASS: whiteboard.task_added
✅ PASS: whiteboard.task_updated
✅ PASS: whiteboard.session_added
✅ PASS: whiteboard.session_removed
✅ PASS: service.started
✅ PASS: service.stopped
✅ PASS: backend.started
✅ PASS: backend.shutdown
✅ PASS: error.occurred
✅ PASS: warning.occurred
✅ PASS: crawl.started
✅ PASS: crawl.completed
✅ PASS: api.request

======================================================================
Testing Noise Filtering
======================================================================
✅ API requests correctly filtered (not published to events)
✅ Critical warnings correctly published
✅ Minor warnings correctly filtered

======================================================================
Test Summary
======================================================================
Passed: 19
Failed: 0
Total: 19

🎉 All tests passed!
```

### Manual Testing

**Monitor events in real-time:**
```bash
docker exec llm-streamer-redis redis-cli
> SUBSCRIBE events:task events:session events:system
```

**Check collector logs:**
```bash
docker compose logs llm-streamer-collector -f | grep "📊 Event detected"
```

## Development

### Adding New Event Patterns

1. **Define pattern** in `event_detector.py`:

```python
"my_event": {
    "pattern": re.compile(r"My log pattern (.+)"),
    "channel": "events:system",
    "event_type": "my.event.type",
    "extract": lambda m: {"field": m.group(1)}
}
```

2. **Add test case** in `test_event_detector.py`:

```python
("My log pattern test123", "events:system", "my.event.type"),
```

3. **Run tests:**
```bash
python test_event_detector.py
```

4. **Restart collector:**
```bash
docker compose restart llm-streamer-collector
```

### Pattern Guidelines

**DO:**
- Use named groups for clarity: `(?P<task_id>[\w-]+)`
- Keep patterns specific to avoid false positives
- Extract meaningful data fields
- Add test cases for each pattern

**DON'T:**
- Use overly broad patterns (e.g., `.*`)
- Capture too much data (affects performance)
- Duplicate existing patterns
- Skip testing

## Monitoring

### View Statistics
```bash
docker compose logs llm-streamer-collector | grep "📈 Archon Log Collector Statistics"
```

**Output:**
```
======================================================================
📈 Archon Log Collector Statistics
======================================================================
Logs published: 1543
Events detected: 47

Events by type:
  task.created: 15
  task.status_changed: 12
  session.started: 8
  whiteboard.task_updated: 7
  service.started: 5
======================================================================
```

### Check Event Detection
```bash
# Recent event detections
docker compose logs llm-streamer-collector --tail 100 | grep "📊 Event detected"

# Example output:
# 📊 Event detected: task.created (entity: task-123) → events:task
```

## Troubleshooting

### No events detected

**Verify collector is running:**
```bash
docker compose ps llm-streamer-collector
# Should show: Up
```

**Check logs are being collected:**
```bash
docker compose logs llm-streamer-collector --tail 50
# Should see log lines from monitored containers
```

**Verify patterns match:**
```bash
python test_event_detector.py
# Should show 19/19 passed
```

### Events not reaching whiteboard

**Check Redis connectivity:**
```bash
docker exec llm-streamer-redis redis-cli PING
# Should show: PONG
```

**Verify EventListenerService is subscribed:**
```bash
docker compose logs archon-server | grep "Subscribed to Redis"
# Should show: ✅ Subscribed to Redis channels: events:task, events:session
```

**Check event processing:**
```bash
docker compose logs archon-server | grep "Event listener"
# Should show processed events
```

## Performance

**Pattern Matching:**
- Regex patterns compiled once at startup
- O(n) complexity per log line
- 18 patterns evaluated per line
- Typical overhead: <1ms per log line

**Memory Usage:**
- Minimal - no log buffering
- Events published immediately
- No message persistence

**Throughput:**
- Handles 100+ logs/second
- Non-blocking async processing
- Scales with Docker log volume

## See Also

- [WHITEBOARD.md](../WHITEBOARD.md) - Complete whiteboard documentation
- [README.md](README.md) - Original LLM Streamer system
- [test_event_detector.py](test_event_detector.py) - Test suite
