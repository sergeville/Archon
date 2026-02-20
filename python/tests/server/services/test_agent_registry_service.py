"""
Unit tests for agent_registry_service.py
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.server.services.agent_registry_service import AgentRegistryService, get_agent_registry_service


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the singleton between tests."""
    import src.server.services.agent_registry_service as ars_module
    original = ars_module._agent_registry_service
    yield
    ars_module._agent_registry_service = original


@pytest.fixture
def agent_service():
    """Create a fresh AgentRegistryService instance with mocked dependencies."""
    with patch("src.server.services.agent_registry_service.get_supabase_client"):
        service = AgentRegistryService()
        return service


@pytest.fixture
def mock_agent_data():
    """Mock agent data matching archon_agent_registry schema."""
    return {
        "id": str(uuid4()),
        "name": "claude",
        "capabilities": ["memory", "coding"],
        "status": "active",
        "last_seen": datetime.now(timezone.utc).isoformat(),
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


# =====================================================
# REGISTER AGENT TESTS
# =====================================================

@pytest.mark.asyncio
async def test_register_agent_success(agent_service, mock_agent_data):
    """Test successful agent registration."""
    mock_response = MagicMock()
    mock_response.data = [mock_agent_data]
    agent_service.supabase.table.return_value.upsert.return_value.execute.return_value = mock_response

    result = await agent_service.register_agent(
        name="claude",
        capabilities=["memory", "coding"],
        metadata={},
    )

    assert result["name"] == "claude"
    assert result["capabilities"] == ["memory", "coding"]
    agent_service.supabase.table.assert_called_with("archon_agent_registry")
    upsert_call = agent_service.supabase.table.return_value.upsert.call_args[0][0]
    assert upsert_call["name"] == "claude"
    assert upsert_call["status"] == "active"


@pytest.mark.asyncio
async def test_register_agent_defaults(agent_service, mock_agent_data):
    """Test registration with default capabilities and metadata."""
    mock_agent_data["capabilities"] = []
    mock_agent_data["metadata"] = {}
    mock_response = MagicMock()
    mock_response.data = [mock_agent_data]
    agent_service.supabase.table.return_value.upsert.return_value.execute.return_value = mock_response

    result = await agent_service.register_agent(name="gemini")

    upsert_call = agent_service.supabase.table.return_value.upsert.call_args[0][0]
    assert upsert_call["capabilities"] == []
    assert upsert_call["metadata"] == {}


@pytest.mark.asyncio
async def test_register_agent_no_data_returned(agent_service):
    """Test that empty response raises exception."""
    mock_response = MagicMock()
    mock_response.data = []
    agent_service.supabase.table.return_value.upsert.return_value.execute.return_value = mock_response

    with pytest.raises(Exception, match="Agent registration returned no data"):
        await agent_service.register_agent(name="claude")


@pytest.mark.asyncio
async def test_register_agent_database_error(agent_service):
    """Test that database errors propagate."""
    agent_service.supabase.table.return_value.upsert.return_value.execute.side_effect = Exception(
        "Connection refused"
    )

    with pytest.raises(Exception, match="Connection refused"):
        await agent_service.register_agent(name="claude")


# =====================================================
# HEARTBEAT TESTS
# =====================================================

@pytest.mark.asyncio
async def test_heartbeat_success(agent_service, mock_agent_data):
    """Test successful heartbeat update."""
    mock_response = MagicMock()
    mock_response.data = [mock_agent_data]

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.execute.return_value = mock_response
    agent_service.supabase.table.return_value.update.return_value = mock_query

    result = await agent_service.heartbeat("claude")

    assert result["name"] == "claude"
    update_call = agent_service.supabase.table.return_value.update.call_args[0][0]
    assert update_call["status"] == "active"
    assert "last_seen" in update_call


@pytest.mark.asyncio
async def test_heartbeat_agent_not_found(agent_service):
    """Test heartbeat raises when agent doesn't exist."""
    mock_response = MagicMock()
    mock_response.data = []

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.execute.return_value = mock_response
    agent_service.supabase.table.return_value.update.return_value = mock_query

    with pytest.raises(Exception, match="not found for heartbeat"):
        await agent_service.heartbeat("unknown_agent")


# =====================================================
# GET AGENT TESTS
# =====================================================

@pytest.mark.asyncio
async def test_get_agent_success(agent_service, mock_agent_data):
    """Test getting an agent by name."""
    mock_response = MagicMock()
    mock_response.data = [mock_agent_data]

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.execute.return_value = mock_response
    agent_service.supabase.table.return_value.select.return_value = mock_query

    result = await agent_service.get_agent("claude")

    assert result["name"] == "claude"
    mock_query.eq.assert_called_with("name", "claude")


@pytest.mark.asyncio
async def test_get_agent_not_found(agent_service):
    """Test that missing agent returns None."""
    mock_response = MagicMock()
    mock_response.data = []

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.execute.return_value = mock_response
    agent_service.supabase.table.return_value.select.return_value = mock_query

    result = await agent_service.get_agent("nonexistent")

    assert result is None


# =====================================================
# LIST AGENTS TESTS
# =====================================================

@pytest.mark.asyncio
async def test_list_agents_no_filter(agent_service, mock_agent_data):
    """Test listing all agents without status filter."""
    mock_response = MagicMock()
    mock_response.data = [mock_agent_data]

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.execute.return_value = mock_response
    agent_service.supabase.table.return_value.select.return_value = mock_query

    result = await agent_service.list_agents()

    assert len(result) == 1
    mock_query.order.assert_called_once_with("last_seen", desc=True)


@pytest.mark.asyncio
async def test_list_agents_with_status_filter(agent_service, mock_agent_data):
    """Test listing agents filtered by status."""
    mock_response = MagicMock()
    mock_response.data = [mock_agent_data]

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.execute.return_value = mock_response
    agent_service.supabase.table.return_value.select.return_value = mock_query

    result = await agent_service.list_agents(status="active")

    mock_query.eq.assert_called_with("status", "active")


@pytest.mark.asyncio
async def test_list_agents_empty(agent_service):
    """Test listing when no agents are registered."""
    mock_response = MagicMock()
    mock_response.data = []

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.execute.return_value = mock_response
    agent_service.supabase.table.return_value.select.return_value = mock_query

    result = await agent_service.list_agents()

    assert result == []


# =====================================================
# DEACTIVATE AGENT TESTS
# =====================================================

@pytest.mark.asyncio
async def test_deactivate_agent_success(agent_service, mock_agent_data):
    """Test successful agent deactivation."""
    mock_agent_data["status"] = "inactive"
    mock_response = MagicMock()
    mock_response.data = [mock_agent_data]

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.execute.return_value = mock_response
    agent_service.supabase.table.return_value.update.return_value = mock_query

    result = await agent_service.deactivate_agent("claude")

    assert result["status"] == "inactive"
    update_call = agent_service.supabase.table.return_value.update.call_args[0][0]
    assert update_call["status"] == "inactive"


@pytest.mark.asyncio
async def test_deactivate_agent_not_found(agent_service):
    """Test deactivation raises when agent not found."""
    mock_response = MagicMock()
    mock_response.data = []

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.execute.return_value = mock_response
    agent_service.supabase.table.return_value.update.return_value = mock_query

    with pytest.raises(Exception, match="not found for deactivation"):
        await agent_service.deactivate_agent("ghost")


# =====================================================
# SINGLETON TESTS
# =====================================================

def test_get_agent_registry_service_singleton():
    """Test that get_agent_registry_service returns the same instance."""
    import src.server.services.agent_registry_service as ars_module
    ars_module._agent_registry_service = None

    with patch("src.server.services.agent_registry_service.get_supabase_client"):
        service1 = get_agent_registry_service()
        service2 = get_agent_registry_service()

    assert service1 is service2


def test_get_agent_registry_service_instance_type():
    """Test that singleton returns an AgentRegistryService instance."""
    import src.server.services.agent_registry_service as ars_module
    ars_module._agent_registry_service = None

    with patch("src.server.services.agent_registry_service.get_supabase_client"):
        service = get_agent_registry_service()

    assert isinstance(service, AgentRegistryService)
