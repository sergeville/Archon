#!/usr/bin/env python3
"""
Test script for event publishing to Redis

Tests:
1. Task creation events
2. Task status change events
3. Session lifecycle events
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import redis.asyncio as redis
from src.server.utils.event_publisher import EventPublisher


async def test_event_publisher():
    """Test EventPublisher functionality"""
    print("=" * 60)
    print("Testing Event Publisher")
    print("=" * 60)

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    print(f"\nConnecting to Redis: {redis_url}")

    # Create Redis subscriber
    subscriber = await redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
    pubsub = subscriber.pubsub()

    # Subscribe to event channels
    await pubsub.subscribe("events:task", "events:session")
    print("✅ Subscribed to channels: events:task, events:session")

    # Create EventPublisher
    event_pub = EventPublisher(redis_url)

    # Start listening for events in background
    received_events = []

    async def event_listener():
        """Background task to listen for events"""
        async for message in pubsub.listen():
            if message["type"] == "message":
                event = json.loads(message["data"])
                received_events.append(event)
                print(f"\n📨 Received {event['event_type']} event:")
                print(f"   Entity: {event['entity_type']} ({event['entity_id']})")
                print(f"   Data: {json.dumps(event['data'], indent=4)}")

    # Start listener
    listener_task = asyncio.create_task(event_listener())

    # Give subscriber time to connect
    await asyncio.sleep(0.5)

    print("\n" + "=" * 60)
    print("Test 1: Publishing task.created event")
    print("=" * 60)

    success = await event_pub.publish_task_event(
        event_type="task.created",
        task_id="test-task-123",
        data={
            "title": "Test Task",
            "assignee": "claude",
            "priority": "high",
            "status": "todo",
            "project_id": "test-project-456"
        },
        agent="claude"
    )
    print(f"✅ Published task.created event: {success}")

    await asyncio.sleep(0.5)

    print("\n" + "=" * 60)
    print("Test 2: Publishing task.status_changed event")
    print("=" * 60)

    success = await event_pub.publish_task_event(
        event_type="task.status_changed",
        task_id="test-task-123",
        data={
            "old_status": "todo",
            "new_status": "doing",
            "title": "Test Task",
            "assignee": "claude",
            "project_id": "test-project-456"
        },
        agent="claude"
    )
    print(f"✅ Published task.status_changed event: {success}")

    await asyncio.sleep(0.5)

    print("\n" + "=" * 60)
    print("Test 3: Publishing session.started event")
    print("=" * 60)

    success = await event_pub.publish_session_event(
        event_type="session.started",
        session_id="test-session-789",
        agent="claude",
        data={
            "project_id": "test-project-456",
            "started_at": "2026-02-16T00:00:00Z"
        }
    )
    print(f"✅ Published session.started event: {success}")

    await asyncio.sleep(0.5)

    print("\n" + "=" * 60)
    print("Test 4: Publishing session.ended event")
    print("=" * 60)

    success = await event_pub.publish_session_event(
        event_type="session.ended",
        session_id="test-session-789",
        agent="claude",
        data={
            "ended_at": "2026-02-16T01:00:00Z",
            "summary": "Test session completed successfully",
            "project_id": "test-project-456"
        }
    )
    print(f"✅ Published session.ended event: {success}")

    # Wait for events to be received
    await asyncio.sleep(1)

    # Cancel listener
    listener_task.cancel()
    try:
        await listener_task
    except asyncio.CancelledError:
        pass

    # Cleanup
    await pubsub.unsubscribe("events:task", "events:session")
    await subscriber.close()

    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    print(f"\n✅ Total events published: 4")
    print(f"✅ Total events received: {len(received_events)}")

    if len(received_events) == 4:
        print("\n🎉 All events successfully published and received!")
        return 0
    else:
        print(f"\n❌ Expected 4 events, received {len(received_events)}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_event_publisher())
    sys.exit(exit_code)
