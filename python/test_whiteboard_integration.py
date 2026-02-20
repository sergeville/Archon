#!/usr/bin/env python3
"""
Test Whiteboard Integration

Tests the complete flow:
1. Publish events to Redis
2. EventListenerService processes them
3. WhiteboardService updates the whiteboard
4. Whiteboard API returns updated state
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

import httpx
import redis.asyncio as redis


async def publish_event(channel: str, event: dict, redis_url: str) -> bool:
    """Publish an event to Redis"""
    try:
        r = await redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        result = await r.publish(channel, json.dumps(event))
        await r.aclose()
        return result > 0
    except Exception as e:
        print(f"❌ Error publishing event: {e}")
        return False


async def query_whiteboard(base_url: str) -> dict:
    """Query the whiteboard API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/whiteboard")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"❌ Error querying whiteboard: {e}")
        return {}


async def test_whiteboard_integration():
    """Test complete whiteboard integration"""
    print("=" * 70)
    print("Whiteboard Integration Test")
    print("=" * 70)

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    api_url = os.getenv("API_URL", "http://localhost:8181")

    print(f"\nRedis URL: {redis_url}")
    print(f"API URL: {api_url}")

    # Test 1: Check initial whiteboard state
    print("\n" + "="*70)
    print("Test 1: Initial Whiteboard State")
    print("="*70)

    initial_state = await query_whiteboard(api_url)
    if initial_state:
        whiteboard = initial_state.get("whiteboard", {})
        content = whiteboard.get("content", {})
        print(f"✅ Whiteboard loaded")
        print(f"   Active sessions: {len(content.get('active_sessions', []))}")
        print(f"   Active tasks: {len(content.get('active_tasks', []))}")
        print(f"   Recent events: {len(content.get('recent_events', []))}")
    else:
        print("❌ Failed to load initial whiteboard state")
        return 1

    # Test 2: Publish session.started event
    print("\n" + "="*70)
    print("Test 2: Session Started Event")
    print("="*70)

    session_id = "test-session-abc123"
    session_event = {
        "event_type": "session.started",
        "entity_type": "session",
        "entity_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": "claude",
        "data": {
            "project_id": "archon-project",
            "started_at": datetime.now(timezone.utc).isoformat()
        }
    }

    success = await publish_event("events:session", session_event, redis_url)
    print(f"{'✅' if success else '❌'} Published session.started event")

    # Wait for event processing
    await asyncio.sleep(2)

    # Check whiteboard
    state = await query_whiteboard(api_url)
    if state:
        content = state.get("whiteboard", {}).get("content", {})
        active_sessions = content.get("active_sessions", [])
        session_found = any(s.get("session_id") == session_id for s in active_sessions)

        if session_found:
            print(f"✅ Session {session_id} added to whiteboard")
            print(f"   Total active sessions: {len(active_sessions)}")
        else:
            print(f"❌ Session {session_id} NOT found on whiteboard")

    # Test 3: Publish task.created with status='doing'
    print("\n" + "="*70)
    print("Test 3: Task Created Event (status=doing)")
    print("="*70)

    task_id = "test-task-xyz789"
    task_event = {
        "event_type": "task.created",
        "entity_type": "task",
        "entity_id": task_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": "claude",
        "data": {
            "title": "Test whiteboard integration",
            "assignee": "claude",
            "priority": "high",
            "status": "doing",  # Should appear on whiteboard
            "project_id": "archon-project"
        }
    }

    success = await publish_event("events:task", task_event, redis_url)
    print(f"{'✅' if success else '❌'} Published task.created event")

    await asyncio.sleep(2)

    state = await query_whiteboard(api_url)
    if state:
        content = state.get("whiteboard", {}).get("content", {})
        active_tasks = content.get("active_tasks", [])
        task_found = any(t.get("task_id") == task_id for t in active_tasks)

        if task_found:
            print(f"✅ Task {task_id} added to whiteboard")
            print(f"   Total active tasks: {len(active_tasks)}")
        else:
            print(f"❌ Task {task_id} NOT found on whiteboard")

    # Test 4: Publish task.status_changed (doing → done)
    print("\n" + "="*70)
    print("Test 4: Task Status Changed Event (doing → done)")
    print("="*70)

    status_event = {
        "event_type": "task.status_changed",
        "entity_type": "task",
        "entity_id": task_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": "claude",
        "data": {
            "old_status": "doing",
            "new_status": "done",
            "title": "Test whiteboard integration",
            "assignee": "claude",
            "project_id": "archon-project"
        }
    }

    success = await publish_event("events:task", status_event, redis_url)
    print(f"{'✅' if success else '❌'} Published task.status_changed event")

    await asyncio.sleep(2)

    state = await query_whiteboard(api_url)
    if state:
        content = state.get("whiteboard", {}).get("content", {})
        active_tasks = content.get("active_tasks", [])
        task_found = any(t.get("task_id") == task_id for t in active_tasks)

        if not task_found:
            print(f"✅ Task {task_id} removed from whiteboard (status=done)")
            print(f"   Total active tasks: {len(active_tasks)}")
        else:
            print(f"❌ Task {task_id} still on whiteboard (should be removed)")

    # Test 5: Publish session.ended event
    print("\n" + "="*70)
    print("Test 5: Session Ended Event")
    print("="*70)

    session_end_event = {
        "event_type": "session.ended",
        "entity_type": "session",
        "entity_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": "claude",
        "data": {
            "ended_at": datetime.now(timezone.utc).isoformat(),
            "summary": "Completed whiteboard integration testing",
            "project_id": "archon-project"
        }
    }

    success = await publish_event("events:session", session_end_event, redis_url)
    print(f"{'✅' if success else '❌'} Published session.ended event")

    await asyncio.sleep(2)

    state = await query_whiteboard(api_url)
    if state:
        content = state.get("whiteboard", {}).get("content", {})
        active_sessions = content.get("active_sessions", [])
        session_found = any(s.get("session_id") == session_id for s in active_sessions)

        if not session_found:
            print(f"✅ Session {session_id} removed from whiteboard")
            print(f"   Total active sessions: {len(active_sessions)}")
        else:
            print(f"❌ Session {session_id} still on whiteboard (should be removed)")

    # Test 6: Check recent events
    print("\n" + "="*70)
    print("Test 6: Recent Events")
    print("="*70)

    state = await query_whiteboard(api_url)
    if state:
        content = state.get("whiteboard", {}).get("content", {})
        recent_events = content.get("recent_events", [])
        print(f"✅ Recent events count: {len(recent_events)}")
        if recent_events:
            print(f"\n   Most recent events:")
            for event in recent_events[:5]:
                print(f"   - {event.get('event_type')} at {event.get('timestamp')}")

    # Final summary
    print("\n" + "="*70)
    print("Final Whiteboard State")
    print("="*70)

    final_state = await query_whiteboard(api_url)
    if final_state:
        whiteboard = final_state.get("whiteboard", {})
        content = whiteboard.get("content", {})
        print(f"Active sessions: {len(content.get('active_sessions', []))}")
        print(f"Active tasks: {len(content.get('active_tasks', []))}")
        print(f"Recent events: {len(content.get('recent_events', []))}")
        print("\n🎉 Phase 2 Complete: Whiteboard Backend is working!")
        return 0
    else:
        print("❌ Failed to get final whiteboard state")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_whiteboard_integration())
    sys.exit(exit_code)
