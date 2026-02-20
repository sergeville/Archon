"""
Unit tests for SessionService.

Tests session CRUD operations, event logging, and semantic search.
"""
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.server.services.session_service import SessionService, get_session_service


# Fixtures

@pytest.fixture
async def session_service():
    """Create a SessionService instance for testing."""
    return SessionService()


@pytest.fixture
async def test_session(session_service):
    """
    Create a test session and clean it up after the test.

    Yields the created session dictionary.
    """
    session = await session_service.create_session(
        agent="test_agent",
        metadata={"test": True}
    )

    yield session

    # Cleanup: Delete test session
    # Note: In real implementation, add a delete method or use SQL directly
    # For now, sessions will be cleaned up manually or with a separate cleanup script


# Test Cases

@pytest.mark.asyncio
async def test_create_session(session_service):
    """Test creating a new session."""
    session = await session_service.create_session(
        agent="claude",
        metadata={"context": "testing"}
    )

    assert session is not None
    assert session["agent"] == "claude"
    assert session["started_at"] is not None
    assert session["ended_at"] is None
    assert session["metadata"]["context"] == "testing"


@pytest.mark.asyncio
async def test_create_session_with_project(session_service):
    """Test creating a session linked to a project."""
    project_id = uuid4()

    session = await session_service.create_session(
        agent="claude",
        project_id=project_id
    )

    assert session["project_id"] == str(project_id)


@pytest.mark.asyncio
async def test_end_session(test_session, session_service):
    """Test ending a session with a summary."""
    session_id = test_session["id"]

    ended = await session_service.end_session(
        session_id=session_id,
        summary="Test session completed successfully"
    )

    assert ended["ended_at"] is not None
    assert ended["summary"] == "Test session completed successfully"
    assert ended["embedding"] is not None  # Should have generated embedding


@pytest.mark.asyncio
async def test_end_session_without_summary(test_session, session_service):
    """Test ending a session without providing a summary."""
    session_id = test_session["id"]

    ended = await session_service.end_session(session_id=session_id)

    assert ended["ended_at"] is not None
    assert ended.get("summary") is None


@pytest.mark.asyncio
async def test_add_event(test_session, session_service):
    """Test logging an event to a session."""
    session_id = test_session["id"]

    event = await session_service.add_event(
        session_id=session_id,
        event_type="task_created",
        event_data={
            "task_id": str(uuid4()),
            "title": "Test task"
        }
    )

    assert event is not None
    assert event["session_id"] == str(session_id)
    assert event["event_type"] == "task_created"
    assert event["event_data"]["title"] == "Test task"
    assert event["timestamp"] is not None


@pytest.mark.asyncio
async def test_add_multiple_events(test_session, session_service):
    """Test logging multiple events to a session."""
    session_id = test_session["id"]

    event_types = ["task_created", "decision_made", "task_completed"]

    for event_type in event_types:
        await session_service.add_event(
            session_id=session_id,
            event_type=event_type,
            event_data={"action": event_type}
        )

    # Retrieve session with events
    session = await session_service.get_session(session_id)

    assert len(session["events"]) == 3
    assert session["events"][0]["event_type"] == "task_created"
    assert session["events"][-1]["event_type"] == "task_completed"


@pytest.mark.asyncio
async def test_get_session(test_session, session_service):
    """Test retrieving a session with its events."""
    session_id = test_session["id"]

    # Add some events
    await session_service.add_event(
        session_id=session_id,
        event_type="test_event",
        event_data={"test": "data"}
    )

    # Retrieve session
    session = await session_service.get_session(session_id)

    assert session is not None
    assert session["id"] == str(session_id)
    assert len(session["events"]) == 1
    assert session["events"][0]["event_type"] == "test_event"


@pytest.mark.asyncio
async def test_get_nonexistent_session(session_service):
    """Test retrieving a session that doesn't exist."""
    fake_id = uuid4()

    session = await session_service.get_session(fake_id)

    assert session is None


@pytest.mark.asyncio
async def test_list_sessions(session_service):
    """Test listing sessions with filters."""
    # Create test sessions
    await session_service.create_session(agent="claude")
    await session_service.create_session(agent="gemini")
    await session_service.create_session(agent="claude")

    # List all sessions
    all_sessions = await session_service.list_sessions(limit=10)
    assert len(all_sessions) >= 3

    # List sessions for specific agent
    claude_sessions = await session_service.list_sessions(
        agent="claude",
        limit=10
    )
    assert all(s["agent"] == "claude" for s in claude_sessions)
    assert len(claude_sessions) >= 2


@pytest.mark.asyncio
async def test_list_sessions_since_date(session_service):
    """Test listing sessions since a specific date."""
    # Create a session
    await session_service.create_session(agent="claude")

    # Query for sessions from last 7 days
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent = await session_service.list_sessions(since=week_ago)

    assert len(recent) >= 1


@pytest.mark.asyncio
async def test_search_sessions(session_service):
    """Test semantic search of sessions."""
    # Create sessions with summaries
    session1 = await session_service.create_session(agent="claude")
    await session_service.end_session(
        session_id=session1["id"],
        summary="Implemented database migration for session tracking"
    )

    session2 = await session_service.create_session(agent="claude")
    await session_service.end_session(
        session_id=session2["id"],
        summary="Fixed authentication bug in API endpoint"
    )

    # Search for database-related sessions
    results = await session_service.search_sessions(
        query="database migration",
        limit=5,
        threshold=0.5
    )

    # Should find the first session
    assert len(results) >= 1
    assert any("database" in r["summary"].lower() for r in results)


@pytest.mark.asyncio
async def test_get_last_session(session_service):
    """Test retrieving the most recent session for an agent."""
    # Create sessions
    await session_service.create_session(agent="test_agent")
    await session_service.create_session(agent="test_agent")
    latest = await session_service.create_session(agent="test_agent")

    # Get last session
    last = await session_service.get_last_session("test_agent")

    assert last is not None
    assert last["id"] == latest["id"]


@pytest.mark.asyncio
async def test_get_last_session_no_sessions(session_service):
    """Test getting last session when none exist."""
    last = await session_service.get_last_session("nonexistent_agent")

    assert last is None


@pytest.mark.asyncio
async def test_count_sessions(session_service):
    """Test counting sessions for an agent."""
    # Create test sessions
    await session_service.create_session(agent="count_test")
    await session_service.create_session(agent="count_test")

    count = await session_service.count_sessions("count_test", days=30)

    assert count >= 2


@pytest.mark.asyncio
async def test_get_recent_sessions(session_service):
    """Test getting recent sessions using database function."""
    # Create test sessions
    await session_service.create_session(agent="recent_test")
    await session_service.create_session(agent="recent_test")

    recent = await session_service.get_recent_sessions(
        agent="recent_test",
        days=7,
        limit=10
    )

    assert len(recent) >= 2
    assert all(s["agent"] == "recent_test" for s in recent)


@pytest.mark.asyncio
async def test_update_session_summary(test_session, session_service):
    """Test updating a session's summary and metadata."""
    session_id = test_session["id"]

    updated = await session_service.update_session_summary(
        session_id=session_id,
        summary="Updated summary with metadata",
        metadata={
            "key_events": ["event1", "event2"],
            "decisions": ["decision1"],
            "outcomes": ["outcome1"],
            "next_steps": ["next1", "next2"]
        }
    )

    assert updated["summary"] == "Updated summary with metadata"
    assert updated["metadata"]["key_events"] == ["event1", "event2"]
    assert updated["metadata"]["decisions"] == ["decision1"]
    assert updated["embedding"] is not None


@pytest.mark.asyncio
async def test_get_active_sessions(session_service):
    """Test getting all active (not ended) sessions."""
    # Create active session
    active = await session_service.create_session(agent="active_test")

    # Create ended session
    ended_session = await session_service.create_session(agent="active_test")
    await session_service.end_session(ended_session["id"])

    # Get active sessions
    active_sessions = await session_service.get_active_sessions()

    # Should include the active session
    active_ids = [s["id"] for s in active_sessions]
    assert active["id"] in active_ids
    assert ended_session["id"] not in active_ids


@pytest.mark.asyncio
async def test_get_session_service_singleton():
    """Test the singleton pattern for SessionService."""
    service1 = get_session_service()
    service2 = get_session_service()

    assert service1 is service2  # Same instance


# Integration Tests

@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_session_lifecycle(session_service):
    """Test complete session lifecycle from creation to search."""
    # 1. Create session
    session = await session_service.create_session(
        agent="claude",
        metadata={"test": "lifecycle"}
    )

    session_id = session["id"]

    # 2. Add events
    await session_service.add_event(
        session_id=session_id,
        event_type="task_created",
        event_data={"task_id": "123", "title": "Test task"}
    )

    await session_service.add_event(
        session_id=session_id,
        event_type="decision_made",
        event_data={"decision": "use pgvector for embeddings"}
    )

    await session_service.add_event(
        session_id=session_id,
        event_type="task_completed",
        event_data={"task_id": "123", "outcome": "success"}
    )

    # 3. End session with summary
    await session_service.end_session(
        session_id=session_id,
        summary="Completed database migration and semantic search implementation"
    )

    # 4. Retrieve session
    retrieved = await session_service.get_session(session_id)
    assert len(retrieved["events"]) == 3
    assert retrieved["summary"] is not None
    assert retrieved["ended_at"] is not None

    # 5. Search for session
    results = await session_service.search_sessions(
        query="database migration",
        threshold=0.5
    )
    assert any(r["id"] == str(session_id) for r in results)

    # 6. Verify it's not in active sessions
    active = await session_service.get_active_sessions()
    assert str(session_id) not in [s["id"] for s in active]


# Performance Tests

@pytest.mark.asyncio
@pytest.mark.performance
async def test_batch_session_creation(session_service):
    """Test creating multiple sessions efficiently."""
    import time

    start = time.time()

    sessions = []
    for i in range(10):
        session = await session_service.create_session(
            agent=f"batch_test_{i % 3}",  # 3 different agents
            metadata={"batch": i}
        )
        sessions.append(session)

    elapsed = time.time() - start

    assert len(sessions) == 10
    assert elapsed < 5.0  # Should complete in under 5 seconds


@pytest.mark.asyncio
@pytest.mark.performance
async def test_search_performance(session_service):
    """Test semantic search performance."""
    import time

    # Ensure we have some sessions with summaries
    for i in range(5):
        session = await session_service.create_session(agent="perf_test")
        await session_service.end_session(
            session_id=session["id"],
            summary=f"Performance test session {i} with various keywords"
        )

    # Test search performance
    start = time.time()
    results = await session_service.search_sessions(
        query="performance test keywords",
        limit=10
    )
    elapsed = time.time() - start

    assert len(results) >= 0  # May or may not find results
    assert elapsed < 2.0  # Should complete in under 2 seconds
