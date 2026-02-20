#!/usr/bin/env python3
"""
Simple standalone test for Redis event publishing

This script tests event publishing without importing server dependencies.
"""

import asyncio
import json
import os
from datetime import datetime, timezone

import redis.asyncio as redis


async def publish_event(channel: str, event: dict, redis_url: str) -> bool:
    """Publish an event to Redis channel"""
    try:
        r = await redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        result = await r.publish(channel, json.dumps(event))
        await r.close()
        return result > 0
    except Exception as e:
        print(f"❌ Error publishing event: {e}")
        return False


async def test_redis_events():
    """Test Redis event publishing and subscription"""
    print("=" * 60)
    print("Redis Event Publishing Test")
    print("=" * 60)

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    print(f"\nConnecting to Redis: {redis_url}\n")

    # Create subscriber
    subscriber = await redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
    pubsub = subscriber.pubsub()

    # Subscribe to channels
    await pubsub.subscribe("events:task", "events:session")
    print("✅ Subscribed to channels: events:task, events:session\n")

    # Track received events
    received_events = []

    async def event_listener():
        """Listen for events"""
        async for message in pubsub.listen():
            if message["type"] == "message":
                event = json.loads(message["data"])
                received_events.append(event)
                print(f"📨 Received {event['event_type']} on {message['channel']}")
                print(f"   Entity: {event['entity_type']} ({event['entity_id']})")
                print(f"   Timestamp: {event['timestamp']}")
                print(f"   Data: {json.dumps(event['data'], indent=6)}\n")

    # Start listener
    listener_task = asyncio.create_task(event_listener())
    await asyncio.sleep(0.5)

    # Test 1: Task created event
    print("Test 1: Publishing task.created event...")
    task_created = {
        "event_type": "task.created",
        "entity_type": "task",
        "entity_id": "test-task-123",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": "claude",
        "data": {
            "title": "Implement whiteboard integration",
            "assignee": "claude",
            "priority": "high",
            "status": "todo",
            "project_id": "archon-project"
        }
    }
    success = await publish_event("events:task", task_created, redis_url)
    print(f"{'✅' if success else '❌'} Task created event published\n")
    await asyncio.sleep(0.5)

    # Test 2: Task status changed event
    print("Test 2: Publishing task.status_changed event...")
    task_status = {
        "event_type": "task.status_changed",
        "entity_type": "task",
        "entity_id": "test-task-123",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": "claude",
        "data": {
            "old_status": "todo",
            "new_status": "doing",
            "title": "Implement whiteboard integration",
            "assignee": "claude",
            "project_id": "archon-project"
        }
    }
    success = await publish_event("events:task", task_status, redis_url)
    print(f"{'✅' if success else '❌'} Task status change event published\n")
    await asyncio.sleep(0.5)

    # Test 3: Session started event
    print("Test 3: Publishing session.started event...")
    session_started = {
        "event_type": "session.started",
        "entity_type": "session",
        "entity_id": "session-abc-789",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": "claude",
        "data": {
            "project_id": "archon-project",
            "started_at": datetime.now(timezone.utc).isoformat()
        }
    }
    success = await publish_event("events:session", session_started, redis_url)
    print(f"{'✅' if success else '❌'} Session started event published\n")
    await asyncio.sleep(0.5)

    # Test 4: Session ended event
    print("Test 4: Publishing session.ended event...")
    session_ended = {
        "event_type": "session.ended",
        "entity_type": "session",
        "entity_id": "session-abc-789",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": "claude",
        "data": {
            "ended_at": datetime.now(timezone.utc).isoformat(),
            "summary": "Completed Phase 1: Event Foundation",
            "project_id": "archon-project"
        }
    }
    success = await publish_event("events:session", session_ended, redis_url)
    print(f"{'✅' if success else '❌'} Session ended event published\n")
    await asyncio.sleep(1)

    # Stop listener
    listener_task.cancel()
    try:
        await listener_task
    except asyncio.CancelledError:
        pass

    # Cleanup
    await pubsub.unsubscribe("events:task", "events:session")
    await subscriber.close()

    # Results
    print("=" * 60)
    print("Test Results")
    print("=" * 60)
    print(f"Published events: 4")
    print(f"Received events: {len(received_events)}")

    if len(received_events) == 4:
        print("\n🎉 SUCCESS: All events published and received correctly!")
        print("\n✅ Phase 1 Complete: Event Foundation is working!")
        return 0
    else:
        print(f"\n❌ FAILURE: Expected 4 events, received {len(received_events)}")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(test_redis_events())
    sys.exit(exit_code)
