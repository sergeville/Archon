"""
Unit tests for shared_context_service.py
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.server.services.shared_context_service import SharedContextService, get_shared_context_service


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the singleton between tests."""
    import src.server.services.shared_context_service as scs_module
    original = scs_module._shared_context_service
    yield
    scs_module._shared_context_service = original


@pytest.fixture
def context_service():
    """Create a fresh SharedContextService instance with mocked dependencies."""
    with patch("src.server.services.shared_context_service.get_supabase_client"):
        service = SharedContextService()
        return service


@pytest.fixture
def mock_context_entry():
    """Mock context entry matching archon_shared_context schema."""
    return {
        "id": str(uuid4()),
        "context_key": "current_project",
        "value": {"name": "archon", "phase": 4},
        "set_by": "claude",
        "session_id": None,
        "expires_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def mock_history_entry():
    """Mock history entry matching archon_shared_context_history schema."""
    return {
        "id": str(uuid4()),
        "context_key": "current_project",
        "old_value": {"name": "old_project"},
        "new_value": {"name": "archon"},
        "changed_by": "claude",
        "changed_at": datetime.now(timezone.utc).isoformat(),
    }


# =====================================================
# SET CONTEXT TESTS
# =====================================================

@pytest.mark.asyncio
async def test_set_context_success(context_service, mock_context_entry):
    """Test successful context upsert."""
    mock_response = MagicMock()
    mock_response.data = [mock_context_entry]
    context_service.supabase.table.return_value.upsert.return_value.execute.return_value = mock_response

    result = await context_service.set_context(
        key="current_project",
        value={"name": "archon"},
        set_by="claude",
    )

    assert result["context_key"] == "current_project"
    context_service.supabase.table.assert_called_with("archon_shared_context")
    upsert_call = context_service.supabase.table.return_value.upsert.call_args[0][0]
    assert upsert_call["context_key"] == "current_project"
    assert upsert_call["set_by"] == "claude"


@pytest.mark.asyncio
async def test_set_context_with_session_and_expiry(context_service, mock_context_entry):
    """Test context set with optional session_id and expires_at."""
    session_id = str(uuid4())
    mock_response = MagicMock()
    mock_response.data = [mock_context_entry]
    context_service.supabase.table.return_value.upsert.return_value.execute.return_value = mock_response

    await context_service.set_context(
        key="current_project",
        value={"name": "archon"},
        set_by="claude",
        session_id=session_id,
        expires_at="2026-12-31T00:00:00Z",
    )

    upsert_call = context_service.supabase.table.return_value.upsert.call_args[0][0]
    assert upsert_call["session_id"] == session_id
    assert upsert_call["expires_at"] == "2026-12-31T00:00:00Z"


@pytest.mark.asyncio
async def test_set_context_without_optional_fields(context_service, mock_context_entry):
    """Test that session_id and expires_at are omitted when not provided."""
    mock_response = MagicMock()
    mock_response.data = [mock_context_entry]
    context_service.supabase.table.return_value.upsert.return_value.execute.return_value = mock_response

    await context_service.set_context(key="flag", value=True, set_by="system")

    upsert_call = context_service.supabase.table.return_value.upsert.call_args[0][0]
    assert "session_id" not in upsert_call
    assert "expires_at" not in upsert_call


@pytest.mark.asyncio
async def test_set_context_no_data_returned(context_service):
    """Test that empty response raises exception."""
    mock_response = MagicMock()
    mock_response.data = []
    context_service.supabase.table.return_value.upsert.return_value.execute.return_value = mock_response

    with pytest.raises(Exception, match="Set context returned no data"):
        await context_service.set_context(key="k", value="v", set_by="claude")


@pytest.mark.asyncio
async def test_set_context_database_error(context_service):
    """Test that database errors propagate."""
    context_service.supabase.table.return_value.upsert.return_value.execute.side_effect = Exception(
        "Unique violation"
    )

    with pytest.raises(Exception, match="Unique violation"):
        await context_service.set_context(key="k", value="v", set_by="claude")


# =====================================================
# GET CONTEXT TESTS
# =====================================================

@pytest.mark.asyncio
async def test_get_context_success(context_service, mock_context_entry):
    """Test getting a context entry by key."""
    mock_response = MagicMock()
    mock_response.data = [mock_context_entry]

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.execute.return_value = mock_response
    context_service.supabase.table.return_value.select.return_value = mock_query

    result = await context_service.get_context("current_project")

    assert result["context_key"] == "current_project"
    mock_query.eq.assert_called_with("context_key", "current_project")


@pytest.mark.asyncio
async def test_get_context_not_found(context_service):
    """Test that missing key returns None."""
    mock_response = MagicMock()
    mock_response.data = []

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.execute.return_value = mock_response
    context_service.supabase.table.return_value.select.return_value = mock_query

    result = await context_service.get_context("missing_key")

    assert result is None


# =====================================================
# LIST CONTEXT TESTS
# =====================================================

@pytest.mark.asyncio
async def test_list_context_no_filter(context_service, mock_context_entry):
    """Test listing all context entries."""
    mock_response = MagicMock()
    mock_response.data = [mock_context_entry]

    mock_query = MagicMock()
    mock_query.like.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.execute.return_value = mock_response
    context_service.supabase.table.return_value.select.return_value = mock_query

    result = await context_service.list_context()

    assert len(result) == 1
    mock_query.order.assert_called_once_with("updated_at", desc=True)


@pytest.mark.asyncio
async def test_list_context_with_prefix(context_service, mock_context_entry):
    """Test listing with prefix filter."""
    mock_response = MagicMock()
    mock_response.data = [mock_context_entry]

    mock_query = MagicMock()
    mock_query.like.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.execute.return_value = mock_response
    context_service.supabase.table.return_value.select.return_value = mock_query

    result = await context_service.list_context(prefix="project/")

    mock_query.like.assert_called_with("context_key", "project/%")


@pytest.mark.asyncio
async def test_list_context_empty(context_service):
    """Test listing when no context entries exist."""
    mock_response = MagicMock()
    mock_response.data = []

    mock_query = MagicMock()
    mock_query.like.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.execute.return_value = mock_response
    context_service.supabase.table.return_value.select.return_value = mock_query

    result = await context_service.list_context()

    assert result == []


# =====================================================
# DELETE CONTEXT TESTS
# =====================================================

@pytest.mark.asyncio
async def test_delete_context_success(context_service, mock_context_entry):
    """Test successful context deletion."""
    mock_response = MagicMock()
    mock_response.data = [mock_context_entry]

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.execute.return_value = mock_response
    context_service.supabase.table.return_value.delete.return_value = mock_query

    result = await context_service.delete_context("current_project")

    assert result is True
    mock_query.eq.assert_called_with("context_key", "current_project")


@pytest.mark.asyncio
async def test_delete_context_not_found(context_service):
    """Test that deleting a missing key returns False."""
    mock_response = MagicMock()
    mock_response.data = []

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.execute.return_value = mock_response
    context_service.supabase.table.return_value.delete.return_value = mock_query

    result = await context_service.delete_context("ghost_key")

    assert result is False


# =====================================================
# GET HISTORY TESTS
# =====================================================

@pytest.mark.asyncio
async def test_get_history_success(context_service, mock_history_entry):
    """Test getting history for a context key."""
    mock_response = MagicMock()
    mock_response.data = [mock_history_entry]

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.execute.return_value = mock_response
    context_service.supabase.table.return_value.select.return_value = mock_query

    result = await context_service.get_history("current_project")

    assert len(result) == 1
    assert result[0]["context_key"] == "current_project"
    context_service.supabase.table.assert_called_with("archon_shared_context_history")
    mock_query.eq.assert_called_with("context_key", "current_project")


@pytest.mark.asyncio
async def test_get_history_with_limit(context_service):
    """Test that custom limit is applied to history query."""
    mock_response = MagicMock()
    mock_response.data = []

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.execute.return_value = mock_response
    context_service.supabase.table.return_value.select.return_value = mock_query

    await context_service.get_history("k", limit=5)

    mock_query.limit.assert_called_once_with(5)


@pytest.mark.asyncio
async def test_get_history_empty(context_service):
    """Test history returns empty list when no changes exist."""
    mock_response = MagicMock()
    mock_response.data = []

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.execute.return_value = mock_response
    context_service.supabase.table.return_value.select.return_value = mock_query

    result = await context_service.get_history("new_key")

    assert result == []


# =====================================================
# SINGLETON TESTS
# =====================================================

def test_get_shared_context_service_singleton():
    """Test that get_shared_context_service returns the same instance."""
    import src.server.services.shared_context_service as scs_module
    scs_module._shared_context_service = None

    with patch("src.server.services.shared_context_service.get_supabase_client"):
        service1 = get_shared_context_service()
        service2 = get_shared_context_service()

    assert service1 is service2


def test_get_shared_context_service_instance_type():
    """Test that singleton returns a SharedContextService instance."""
    import src.server.services.shared_context_service as scs_module
    scs_module._shared_context_service = None

    with patch("src.server.services.shared_context_service.get_supabase_client"):
        service = get_shared_context_service()

    assert isinstance(service, SharedContextService)
