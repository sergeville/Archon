"""
Unit tests for memory_service.py
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from src.server.services.memory_service import MemoryService, get_memory_service


@pytest.fixture
def memory_service():
    """Create a fresh memory service instance for each test."""
    with patch("src.server.services.memory_service.get_supabase_client"), \
         patch("src.server.services.memory_service.get_embedding_service"), \
         patch("src.server.services.memory_service.SessionService"):
        service = MemoryService()
        return service


@pytest.fixture
def mock_session_data():
    """Mock session data."""
    return {
        "id": str(uuid4()),
        "agent": "claude",
        "project_id": None,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "ended_at": None,
        "summary": None,
        "context": {"working_on": "Phase 2"},
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def mock_message_data():
    """Mock conversation message data."""
    return {
        "id": str(uuid4()),
        "session_id": str(uuid4()),
        "role": "user",
        "message": "Create a database migration",
        "tools_used": [],
        "type": "command",
        "subtype": "task_request",
        "embedding": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {}
    }


# =====================================================
# CREATE SESSION TESTS
# =====================================================

@pytest.mark.asyncio
async def test_create_session_delegates_to_session_service(memory_service, mock_session_data):
    """Test that create_session delegates to SessionService."""
    memory_service.session_service.create_session = AsyncMock(return_value=mock_session_data)

    result = await memory_service.create_session(
        agent="claude",
        context={"working_on": "Phase 2"}
    )

    assert result == mock_session_data
    memory_service.session_service.create_session.assert_called_once_with(
        agent="claude",
        project_id=None,
        context={"working_on": "Phase 2"},
        metadata=None
    )


@pytest.mark.asyncio
async def test_create_session_with_project(memory_service, mock_session_data):
    """Test create_session with project_id."""
    project_id = uuid4()
    mock_session_data["project_id"] = str(project_id)
    memory_service.session_service.create_session = AsyncMock(return_value=mock_session_data)

    result = await memory_service.create_session(
        agent="claude",
        project_id=project_id
    )

    assert result["project_id"] == str(project_id)
    memory_service.session_service.create_session.assert_called_once()


# =====================================================
# END SESSION TESTS
# =====================================================

@pytest.mark.asyncio
async def test_end_session_delegates_to_session_service(memory_service, mock_session_data):
    """Test that end_session delegates to SessionService."""
    session_id = UUID(mock_session_data["id"])
    mock_session_data["ended_at"] = datetime.now(timezone.utc).isoformat()
    mock_session_data["summary"] = "Completed Phase 2 tasks"

    memory_service.session_service.end_session = AsyncMock(return_value=mock_session_data)

    result = await memory_service.end_session(
        session_id=session_id,
        summary="Completed Phase 2 tasks"
    )

    assert result["ended_at"] is not None
    assert result["summary"] == "Completed Phase 2 tasks"
    memory_service.session_service.end_session.assert_called_once_with(
        session_id=session_id,
        summary="Completed Phase 2 tasks",
        metadata=None
    )


# =====================================================
# STORE MESSAGE TESTS
# =====================================================

@pytest.mark.asyncio
async def test_store_message_user_success(memory_service, mock_message_data):
    """Test storing a user message successfully."""
    session_id = UUID(mock_message_data["session_id"])

    # Mock Supabase insert
    mock_response = MagicMock()
    mock_response.data = [mock_message_data]
    memory_service.supabase.table.return_value.insert.return_value.execute.return_value = mock_response

    # Mock embedding service
    memory_service.embedding_service.generate_embedding = AsyncMock(
        return_value=[0.1] * 1536
    )

    result = await memory_service.store_message(
        session_id=session_id,
        role="user",
        message="Create a database migration",
        message_type="command",
        subtype="task_request"
    )

    assert result["id"] == mock_message_data["id"]
    assert result["role"] == "user"
    assert result["message"] == "Create a database migration"
    memory_service.supabase.table.assert_called_with("conversation_history")
    memory_service.embedding_service.generate_embedding.assert_called_once()


@pytest.mark.asyncio
async def test_store_message_assistant_with_tools(memory_service, mock_message_data):
    """Test storing an assistant message with tools_used."""
    session_id = UUID(mock_message_data["session_id"])
    mock_message_data["role"] = "assistant"
    mock_message_data["tools_used"] = ["database", "migration"]

    mock_response = MagicMock()
    mock_response.data = [mock_message_data]
    memory_service.supabase.table.return_value.insert.return_value.execute.return_value = mock_response

    memory_service.embedding_service.generate_embedding = AsyncMock(
        return_value=[0.1] * 1536
    )

    result = await memory_service.store_message(
        session_id=session_id,
        role="assistant",
        message="I'll create the migration.",
        tools_used=["database", "migration"]
    )

    assert result["role"] == "assistant"
    assert result["tools_used"] == ["database", "migration"]


@pytest.mark.asyncio
async def test_store_message_invalid_role(memory_service):
    """Test that invalid role raises ValueError."""
    session_id = uuid4()

    with pytest.raises(ValueError, match="Invalid role"):
        await memory_service.store_message(
            session_id=session_id,
            role="invalid_role",
            message="test"
        )


@pytest.mark.asyncio
async def test_store_message_without_embedding(memory_service, mock_message_data):
    """Test storing message without generating embedding."""
    session_id = UUID(mock_message_data["session_id"])

    mock_response = MagicMock()
    mock_response.data = [mock_message_data]
    memory_service.supabase.table.return_value.insert.return_value.execute.return_value = mock_response

    result = await memory_service.store_message(
        session_id=session_id,
        role="user",
        message="test message",
        generate_embedding=False
    )

    assert result is not None
    # Embedding service should not be called
    memory_service.embedding_service.generate_embedding.assert_not_called()


@pytest.mark.asyncio
async def test_store_message_embedding_failure_continues(memory_service, mock_message_data):
    """Test that embedding failure doesn't prevent message storage."""
    session_id = UUID(mock_message_data["session_id"])

    mock_response = MagicMock()
    mock_response.data = [mock_message_data]
    memory_service.supabase.table.return_value.insert.return_value.execute.return_value = mock_response

    # Mock embedding failure
    memory_service.embedding_service.generate_embedding = AsyncMock(
        side_effect=Exception("Embedding service down")
    )

    # Should still succeed without embedding
    result = await memory_service.store_message(
        session_id=session_id,
        role="user",
        message="test message"
    )

    assert result is not None


# =====================================================
# GET SESSION HISTORY TESTS
# =====================================================

@pytest.mark.asyncio
async def test_get_session_history_success(memory_service):
    """Test retrieving conversation history for a session."""
    session_id = uuid4()
    mock_messages = [
        {
            "id": str(uuid4()),
            "session_id": str(session_id),
            "role": "user",
            "message": "First message",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid4()),
            "session_id": str(session_id),
            "role": "assistant",
            "message": "Second message",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]

    # Mock Supabase query chain
    mock_response = MagicMock()
    mock_response.data = mock_messages

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.execute.return_value = mock_response

    memory_service.supabase.table.return_value.select.return_value = mock_query

    result = await memory_service.get_session_history(session_id=session_id)

    assert len(result) == 2
    assert result[0]["role"] == "user"
    assert result[1]["role"] == "assistant"
    memory_service.supabase.table.assert_called_with("conversation_history")


@pytest.mark.asyncio
async def test_get_session_history_with_role_filter(memory_service):
    """Test retrieving only user messages."""
    session_id = uuid4()
    mock_messages = [
        {
            "id": str(uuid4()),
            "session_id": str(session_id),
            "role": "user",
            "message": "User message",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]

    mock_response = MagicMock()
    mock_response.data = mock_messages

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.execute.return_value = mock_response

    memory_service.supabase.table.return_value.select.return_value = mock_query

    result = await memory_service.get_session_history(
        session_id=session_id,
        role_filter="user"
    )

    assert len(result) == 1
    assert result[0]["role"] == "user"
    # Verify role filter was applied
    assert mock_query.eq.call_count == 2  # session_id and role


@pytest.mark.asyncio
async def test_get_session_history_with_limit(memory_service):
    """Test limiting number of messages returned."""
    session_id = uuid4()
    mock_messages = []  # Empty list is fine for this test

    mock_response = MagicMock()
    mock_response.data = mock_messages

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.execute.return_value = mock_response

    memory_service.supabase.table.return_value.select.return_value = mock_query

    await memory_service.get_session_history(session_id=session_id, limit=10)

    # Verify limit was called with 10
    mock_query.limit.assert_called_with(10)


@pytest.mark.asyncio
async def test_get_session_history_empty_result(memory_service):
    """Test handling of empty conversation history."""
    session_id = uuid4()

    mock_response = MagicMock()
    mock_response.data = []

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.execute.return_value = mock_response

    memory_service.supabase.table.return_value.select.return_value = mock_query

    result = await memory_service.get_session_history(session_id=session_id)

    assert result == []


# =====================================================
# SEARCH CONVERSATIONS TESTS
# =====================================================

@pytest.mark.asyncio
async def test_search_conversations_success(memory_service):
    """Test semantic search of conversations."""
    mock_results = [
        {
            "id": str(uuid4()),
            "session_id": str(uuid4()),
            "role": "user",
            "message": "Database migration issues",
            "similarity": 0.85,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid4()),
            "session_id": str(uuid4()),
            "role": "assistant",
            "message": "Let me help with the migration",
            "similarity": 0.78,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]

    # Mock embedding generation
    memory_service.embedding_service.generate_embedding = AsyncMock(
        return_value=[0.1] * 1536
    )

    # Mock RPC call
    mock_response = MagicMock()
    mock_response.data = mock_results
    memory_service.supabase.rpc.return_value.execute.return_value = mock_response

    result = await memory_service.search_conversations(
        query="database migration problems"
    )

    assert len(result) == 2
    assert result[0]["similarity"] >= result[1]["similarity"]  # Ordered by similarity
    memory_service.embedding_service.generate_embedding.assert_called_once()
    memory_service.supabase.rpc.assert_called_with(
        "search_conversation_semantic",
        {
            "p_query_embedding": [0.1] * 1536,
            "p_match_count": 10,
            "p_threshold": 0.7
        }
    )


@pytest.mark.asyncio
async def test_search_conversations_with_session_filter(memory_service):
    """Test searching within specific session."""
    session_id = uuid4()
    mock_results = []

    memory_service.embedding_service.generate_embedding = AsyncMock(
        return_value=[0.1] * 1536
    )

    mock_response = MagicMock()
    mock_response.data = mock_results
    memory_service.supabase.rpc.return_value.execute.return_value = mock_response

    await memory_service.search_conversations(
        query="test query",
        session_id=session_id
    )

    # Verify session_id was included in RPC params
    call_args = memory_service.supabase.rpc.call_args[0][1]
    assert call_args["p_session_id"] == str(session_id)


@pytest.mark.asyncio
async def test_search_conversations_with_role_filter(memory_service):
    """Test filtering search results by role."""
    mock_results = [
        {
            "id": str(uuid4()),
            "role": "user",
            "message": "User message",
            "similarity": 0.9
        },
        {
            "id": str(uuid4()),
            "role": "assistant",
            "message": "Assistant message",
            "similarity": 0.85
        }
    ]

    memory_service.embedding_service.generate_embedding = AsyncMock(
        return_value=[0.1] * 1536
    )

    mock_response = MagicMock()
    mock_response.data = mock_results
    memory_service.supabase.rpc.return_value.execute.return_value = mock_response

    result = await memory_service.search_conversations(
        query="test",
        role_filter="user"
    )

    # Should only return user messages
    assert len(result) == 1
    assert result[0]["role"] == "user"


@pytest.mark.asyncio
async def test_search_conversations_custom_threshold(memory_service):
    """Test using custom similarity threshold."""
    memory_service.embedding_service.generate_embedding = AsyncMock(
        return_value=[0.1] * 1536
    )

    mock_response = MagicMock()
    mock_response.data = []
    memory_service.supabase.rpc.return_value.execute.return_value = mock_response

    await memory_service.search_conversations(
        query="test",
        similarity_threshold=0.9
    )

    # Verify threshold was passed
    call_args = memory_service.supabase.rpc.call_args[0][1]
    assert call_args["p_threshold"] == 0.9


# =====================================================
# SINGLETON TESTS
# =====================================================

def test_get_memory_service_singleton():
    """Test that get_memory_service returns singleton instance."""
    with patch("src.server.services.memory_service.get_supabase_client"), \
         patch("src.server.services.memory_service.get_embedding_service"), \
         patch("src.server.services.memory_service.SessionService"):

        service1 = get_memory_service()
        service2 = get_memory_service()

        assert service1 is service2


# =====================================================
# ERROR HANDLING TESTS
# =====================================================

@pytest.mark.asyncio
async def test_store_message_database_error(memory_service):
    """Test handling of database errors during message storage."""
    session_id = uuid4()

    memory_service.embedding_service.generate_embedding = AsyncMock(
        return_value=[0.1] * 1536
    )

    # Mock database error
    memory_service.supabase.table.return_value.insert.return_value.execute.side_effect = Exception(
        "Database error"
    )

    with pytest.raises(Exception, match="Database error"):
        await memory_service.store_message(
            session_id=session_id,
            role="user",
            message="test"
        )


@pytest.mark.asyncio
async def test_get_session_history_database_error(memory_service):
    """Test handling of database errors during history retrieval."""
    session_id = uuid4()

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.execute.side_effect = Exception("Database error")

    memory_service.supabase.table.return_value.select.return_value = mock_query

    with pytest.raises(Exception, match="Database error"):
        await memory_service.get_session_history(session_id=session_id)


@pytest.mark.asyncio
async def test_search_conversations_embedding_error(memory_service):
    """Test handling of embedding generation errors."""
    memory_service.embedding_service.generate_embedding = AsyncMock(
        side_effect=Exception("Embedding service error")
    )

    with pytest.raises(Exception, match="Embedding service error"):
        await memory_service.search_conversations(query="test")
