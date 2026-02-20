"""
Unit tests for handoff_service.py
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.server.services.handoff_service import HandoffService, get_handoff_service


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the singleton between tests."""
    import src.server.services.handoff_service as hs_module
    original = hs_module._handoff_service
    yield
    hs_module._handoff_service = original


@pytest.fixture
def handoff_service():
    """Create a fresh HandoffService instance with mocked dependencies."""
    with patch("src.server.services.handoff_service.get_supabase_client"):
        service = HandoffService()
        return service


@pytest.fixture
def mock_handoff_data():
    """Mock handoff data matching archon_session_handoffs schema."""
    return {
        "id": str(uuid4()),
        "session_id": str(uuid4()),
        "from_agent": "claude",
        "to_agent": "gemini",
        "context": {"task": "finish phase 4"},
        "notes": "Pick up from step 6",
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "accepted_at": None,
        "completed_at": None,
        "metadata": {},
    }


# =====================================================
# CREATE HANDOFF TESTS
# =====================================================

@pytest.mark.asyncio
async def test_create_handoff_success(handoff_service, mock_handoff_data):
    """Test successful handoff creation."""
    mock_response = MagicMock()
    mock_response.data = [mock_handoff_data]
    handoff_service.supabase.table.return_value.insert.return_value.execute.return_value = mock_response

    result = await handoff_service.create_handoff(
        session_id=mock_handoff_data["session_id"],
        from_agent="claude",
        to_agent="gemini",
        context={"task": "finish phase 4"},
        notes="Pick up from step 6",
    )

    assert result["from_agent"] == "claude"
    assert result["to_agent"] == "gemini"
    assert result["status"] == "pending"
    handoff_service.supabase.table.assert_called_with("archon_session_handoffs")


@pytest.mark.asyncio
async def test_create_handoff_defaults(handoff_service, mock_handoff_data):
    """Test handoff creation with minimal required fields."""
    mock_handoff_data["context"] = {}
    mock_handoff_data["notes"] = None
    mock_response = MagicMock()
    mock_response.data = [mock_handoff_data]
    handoff_service.supabase.table.return_value.insert.return_value.execute.return_value = mock_response

    result = await handoff_service.create_handoff(
        session_id=mock_handoff_data["session_id"],
        from_agent="claude",
        to_agent="gemini",
    )

    insert_call = handoff_service.supabase.table.return_value.insert.call_args[0][0]
    assert insert_call["context"] == {}
    assert insert_call["notes"] is None
    assert insert_call["status"] == "pending"


@pytest.mark.asyncio
async def test_create_handoff_no_data_returned(handoff_service):
    """Test that empty response raises exception."""
    mock_response = MagicMock()
    mock_response.data = []
    handoff_service.supabase.table.return_value.insert.return_value.execute.return_value = mock_response

    with pytest.raises(Exception, match="Handoff creation returned no data"):
        await handoff_service.create_handoff(
            session_id=str(uuid4()),
            from_agent="claude",
            to_agent="gemini",
        )


@pytest.mark.asyncio
async def test_create_handoff_database_error(handoff_service):
    """Test that database errors propagate."""
    handoff_service.supabase.table.return_value.insert.return_value.execute.side_effect = Exception(
        "FK violation"
    )

    with pytest.raises(Exception, match="FK violation"):
        await handoff_service.create_handoff(
            session_id=str(uuid4()),
            from_agent="claude",
            to_agent="gemini",
        )


# =====================================================
# ACCEPT HANDOFF TESTS
# =====================================================

@pytest.mark.asyncio
async def test_accept_handoff_success(handoff_service, mock_handoff_data):
    """Test accepting a pending handoff."""
    mock_handoff_data["status"] = "accepted"
    mock_handoff_data["accepted_at"] = datetime.now(timezone.utc).isoformat()
    mock_response = MagicMock()
    mock_response.data = [mock_handoff_data]

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.execute.return_value = mock_response
    handoff_service.supabase.table.return_value.update.return_value = mock_query

    handoff_id = mock_handoff_data["id"]
    result = await handoff_service.accept_handoff(handoff_id)

    assert result["status"] == "accepted"
    update_call = handoff_service.supabase.table.return_value.update.call_args[0][0]
    assert update_call["status"] == "accepted"
    assert "accepted_at" in update_call


@pytest.mark.asyncio
async def test_accept_handoff_not_found(handoff_service):
    """Test accept raises when handoff not found."""
    mock_response = MagicMock()
    mock_response.data = []

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.execute.return_value = mock_response
    handoff_service.supabase.table.return_value.update.return_value = mock_query

    with pytest.raises(Exception, match="not found for acceptance"):
        await handoff_service.accept_handoff(str(uuid4()))


# =====================================================
# COMPLETE HANDOFF TESTS
# =====================================================

@pytest.mark.asyncio
async def test_complete_handoff_success(handoff_service, mock_handoff_data):
    """Test completing an accepted handoff."""
    mock_handoff_data["status"] = "completed"
    mock_handoff_data["completed_at"] = datetime.now(timezone.utc).isoformat()
    mock_response = MagicMock()
    mock_response.data = [mock_handoff_data]

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.execute.return_value = mock_response
    handoff_service.supabase.table.return_value.update.return_value = mock_query

    result = await handoff_service.complete_handoff(mock_handoff_data["id"])

    assert result["status"] == "completed"
    update_call = handoff_service.supabase.table.return_value.update.call_args[0][0]
    assert update_call["status"] == "completed"
    assert "completed_at" in update_call


@pytest.mark.asyncio
async def test_complete_handoff_not_found(handoff_service):
    """Test complete raises when handoff not found."""
    mock_response = MagicMock()
    mock_response.data = []

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.execute.return_value = mock_response
    handoff_service.supabase.table.return_value.update.return_value = mock_query

    with pytest.raises(Exception, match="not found for completion"):
        await handoff_service.complete_handoff(str(uuid4()))


# =====================================================
# REJECT HANDOFF TESTS
# =====================================================

@pytest.mark.asyncio
async def test_reject_handoff_success(handoff_service, mock_handoff_data):
    """Test rejecting a pending handoff."""
    mock_handoff_data["status"] = "rejected"
    mock_response = MagicMock()
    mock_response.data = [mock_handoff_data]

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.execute.return_value = mock_response
    handoff_service.supabase.table.return_value.update.return_value = mock_query

    result = await handoff_service.reject_handoff(mock_handoff_data["id"])

    assert result["status"] == "rejected"
    update_call = handoff_service.supabase.table.return_value.update.call_args[0][0]
    assert update_call["status"] == "rejected"


@pytest.mark.asyncio
async def test_reject_handoff_not_found(handoff_service):
    """Test reject raises when handoff not found."""
    mock_response = MagicMock()
    mock_response.data = []

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.execute.return_value = mock_response
    handoff_service.supabase.table.return_value.update.return_value = mock_query

    with pytest.raises(Exception, match="not found for rejection"):
        await handoff_service.reject_handoff(str(uuid4()))


# =====================================================
# GET PENDING HANDOFFS TESTS
# =====================================================

@pytest.mark.asyncio
async def test_get_pending_handoffs_success(handoff_service, mock_handoff_data):
    """Test getting pending handoffs for an agent."""
    mock_response = MagicMock()
    mock_response.data = [mock_handoff_data]

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.execute.return_value = mock_response
    handoff_service.supabase.table.return_value.select.return_value = mock_query

    result = await handoff_service.get_pending_handoffs("gemini")

    assert len(result) == 1
    calls = mock_query.eq.call_args_list
    call_args = [(c[0][0], c[0][1]) for c in calls]
    assert ("to_agent", "gemini") in call_args
    assert ("status", "pending") in call_args


@pytest.mark.asyncio
async def test_get_pending_handoffs_empty(handoff_service):
    """Test no pending handoffs returns empty list."""
    mock_response = MagicMock()
    mock_response.data = []

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.execute.return_value = mock_response
    handoff_service.supabase.table.return_value.select.return_value = mock_query

    result = await handoff_service.get_pending_handoffs("claude")

    assert result == []


# =====================================================
# GET HANDOFF TESTS
# =====================================================

@pytest.mark.asyncio
async def test_get_handoff_success(handoff_service, mock_handoff_data):
    """Test getting a handoff by ID."""
    mock_response = MagicMock()
    mock_response.data = [mock_handoff_data]

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.execute.return_value = mock_response
    handoff_service.supabase.table.return_value.select.return_value = mock_query

    result = await handoff_service.get_handoff(mock_handoff_data["id"])

    assert result["id"] == mock_handoff_data["id"]


@pytest.mark.asyncio
async def test_get_handoff_not_found(handoff_service):
    """Test that missing handoff returns None."""
    mock_response = MagicMock()
    mock_response.data = []

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.execute.return_value = mock_response
    handoff_service.supabase.table.return_value.select.return_value = mock_query

    result = await handoff_service.get_handoff(str(uuid4()))

    assert result is None


# =====================================================
# LIST HANDOFFS TESTS
# =====================================================

@pytest.mark.asyncio
async def test_list_handoffs_no_filters(handoff_service, mock_handoff_data):
    """Test listing all handoffs without filters."""
    mock_response = MagicMock()
    mock_response.data = [mock_handoff_data]

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.execute.return_value = mock_response
    handoff_service.supabase.table.return_value.select.return_value = mock_query

    result = await handoff_service.list_handoffs()

    assert len(result) == 1
    mock_query.order.assert_called_once_with("created_at", desc=True)


@pytest.mark.asyncio
async def test_list_handoffs_with_filters(handoff_service, mock_handoff_data):
    """Test listing handoffs with all filters applied."""
    mock_response = MagicMock()
    mock_response.data = [mock_handoff_data]

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.execute.return_value = mock_response
    handoff_service.supabase.table.return_value.select.return_value = mock_query

    session_id = str(uuid4())
    await handoff_service.list_handoffs(session_id=session_id, agent="gemini", status="pending")

    calls = mock_query.eq.call_args_list
    call_args = [(c[0][0], c[0][1]) for c in calls]
    assert ("session_id", session_id) in call_args
    assert ("to_agent", "gemini") in call_args
    assert ("status", "pending") in call_args


@pytest.mark.asyncio
async def test_list_handoffs_empty(handoff_service):
    """Test listing when no handoffs exist."""
    mock_response = MagicMock()
    mock_response.data = []

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.execute.return_value = mock_response
    handoff_service.supabase.table.return_value.select.return_value = mock_query

    result = await handoff_service.list_handoffs()

    assert result == []


# =====================================================
# SINGLETON TESTS
# =====================================================

def test_get_handoff_service_singleton():
    """Test that get_handoff_service returns the same instance."""
    import src.server.services.handoff_service as hs_module
    hs_module._handoff_service = None

    with patch("src.server.services.handoff_service.get_supabase_client"):
        service1 = get_handoff_service()
        service2 = get_handoff_service()

    assert service1 is service2


def test_get_handoff_service_instance_type():
    """Test that singleton returns a HandoffService instance."""
    import src.server.services.handoff_service as hs_module
    hs_module._handoff_service = None

    with patch("src.server.services.handoff_service.get_supabase_client"):
        service = get_handoff_service()

    assert isinstance(service, HandoffService)
