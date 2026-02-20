"""Unit tests for pattern management MCP tools (find_patterns + manage_pattern)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from mcp.server.fastmcp import Context

from src.mcp_server.features.patterns.pattern_tools import (
    optimize_pattern_response,
    register_pattern_tools,
    truncate_text,
)


# =====================================================
# FIXTURES
# =====================================================

@pytest.fixture
def mock_mcp():
    """Create a mock MCP server that captures registered tools."""
    mock = MagicMock()
    mock._tools = {}

    def tool_decorator():
        def decorator(func):
            mock._tools[func.__name__] = func
            return func
        return decorator

    mock.tool = tool_decorator
    return mock


@pytest.fixture
def mock_context():
    """Create a mock MCP context."""
    return MagicMock(spec=Context)


@pytest.fixture
def mock_pattern():
    """Sample pattern dict as returned by the API."""
    return {
        "id": str(uuid4()),
        "pattern_type": "technical",
        "domain": "database",
        "description": "Index frequently queried columns for performance",
        "action": "Create B-tree index on foreign keys and filter columns",
        "outcome": "Query time reduced by 60-80%",
        "context": {"technology": "PostgreSQL"},
        "embedding": [0.1] * 1536,
        "metadata": {"confidence": 0.9},
        "created_by": "claude",
    }


# =====================================================
# HELPER FUNCTION TESTS
# =====================================================

def test_truncate_text_short_string():
    """Text shorter than max_length is returned unchanged."""
    result = truncate_text("short text")
    assert result == "short text"


def test_truncate_text_long_string():
    """Text longer than 1000 chars is truncated with ellipsis."""
    long_text = "x" * 1100
    result = truncate_text(long_text)
    assert len(result) == 1000
    assert result.endswith("...")


def test_truncate_text_custom_max():
    """Custom max_length is respected."""
    result = truncate_text("hello world", max_length=8)
    assert result == "hello..."
    assert len(result) == 8


def test_truncate_text_empty_string():
    """Empty string returned as-is."""
    assert truncate_text("") == ""


def test_optimize_pattern_response_strips_embedding(mock_pattern):
    """optimize_pattern_response removes the embedding vector."""
    result = optimize_pattern_response(mock_pattern)
    assert "embedding" not in result


def test_optimize_pattern_response_does_not_mutate_original(mock_pattern):
    """Original pattern dict is not modified."""
    optimize_pattern_response(mock_pattern)
    assert "embedding" in mock_pattern


def test_optimize_pattern_response_truncates_long_description():
    """Descriptions over 1000 chars are truncated."""
    pattern = {
        "description": "d" * 1200,
        "action": "some action",
    }
    result = optimize_pattern_response(pattern)
    assert len(result["description"]) == 1000
    assert result["description"].endswith("...")


def test_optimize_pattern_response_no_embedding_key():
    """Pattern without embedding key is handled gracefully."""
    pattern = {"description": "desc", "action": "act"}
    result = optimize_pattern_response(pattern)
    assert "embedding" not in result
    assert result["description"] == "desc"


# =====================================================
# TOOL REGISTRATION TESTS
# =====================================================

def test_find_patterns_tool_is_registered(mock_mcp):
    """find_patterns tool is registered on the MCP server."""
    register_pattern_tools(mock_mcp)
    assert "find_patterns" in mock_mcp._tools


def test_manage_pattern_tool_is_registered(mock_mcp):
    """manage_pattern tool is registered on the MCP server."""
    register_pattern_tools(mock_mcp)
    assert "manage_pattern" in mock_mcp._tools


# =====================================================
# FIND PATTERNS — GET BY ID
# =====================================================

@pytest.mark.asyncio
async def test_find_patterns_by_id_success(mock_mcp, mock_context, mock_pattern):
    """find_patterns with pattern_id fetches GET /api/patterns/{id}."""
    register_pattern_tools(mock_mcp)
    find_patterns = mock_mcp._tools["find_patterns"]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"pattern": mock_pattern}

    with patch("src.mcp_server.features.patterns.pattern_tools.httpx.AsyncClient") as mock_client:
        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_async_client

        result = await find_patterns(mock_context, pattern_id=mock_pattern["id"])

    data = json.loads(result)
    assert data["success"] is True
    assert "pattern" in data
    assert "embedding" not in data["pattern"]

    # Confirm GET was called with the right path segment
    call_url = mock_async_client.get.call_args[0][0]
    assert mock_pattern["id"] in call_url


@pytest.mark.asyncio
async def test_find_patterns_by_id_not_found(mock_mcp, mock_context):
    """find_patterns with unknown ID returns error from API."""
    register_pattern_tools(mock_mcp)
    find_patterns = mock_mcp._tools["find_patterns"]

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Pattern not found"

    with patch("src.mcp_server.features.patterns.pattern_tools.httpx.AsyncClient") as mock_client:
        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_async_client

        result = await find_patterns(mock_context, pattern_id=str(uuid4()))

    data = json.loads(result)
    assert data["success"] is False
    assert "error" in data


# =====================================================
# FIND PATTERNS — SEMANTIC SEARCH
# =====================================================

@pytest.mark.asyncio
async def test_find_patterns_semantic_search_success(mock_mcp, mock_context, mock_pattern):
    """find_patterns with query sends POST /api/patterns/search."""
    register_pattern_tools(mock_mcp)
    find_patterns = mock_mcp._tools["find_patterns"]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"patterns": [mock_pattern, mock_pattern]}

    with patch("src.mcp_server.features.patterns.pattern_tools.httpx.AsyncClient") as mock_client:
        mock_async_client = AsyncMock()
        mock_async_client.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_async_client

        result = await find_patterns(
            mock_context,
            query="database query optimization",
            limit=5,
            threshold=0.8,
        )

    data = json.loads(result)
    assert data["success"] is True
    assert data["mode"] == "semantic_search"
    assert data["count"] == 2
    for p in data["patterns"]:
        assert "embedding" not in p

    # Confirm POST was made with search parameters
    call_args = mock_async_client.post.call_args
    assert "/api/patterns/search" in call_args[0][0]
    sent_data = call_args[1]["json"]
    assert sent_data["query"] == "database query optimization"
    assert sent_data["limit"] == 5
    assert sent_data["threshold"] == 0.8


@pytest.mark.asyncio
async def test_find_patterns_semantic_search_with_domain(mock_mcp, mock_context, mock_pattern):
    """find_patterns semantic search passes domain filter."""
    register_pattern_tools(mock_mcp)
    find_patterns = mock_mcp._tools["find_patterns"]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"patterns": [mock_pattern]}

    with patch("src.mcp_server.features.patterns.pattern_tools.httpx.AsyncClient") as mock_client:
        mock_async_client = AsyncMock()
        mock_async_client.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_async_client

        result = await find_patterns(
            mock_context,
            query="performance",
            domain="database",
        )

    data = json.loads(result)
    assert data["success"] is True

    sent_data = mock_async_client.post.call_args[1]["json"]
    assert sent_data["domain"] == "database"


@pytest.mark.asyncio
async def test_find_patterns_semantic_search_empty_results(mock_mcp, mock_context):
    """find_patterns semantic search returns zero-count when no matches."""
    register_pattern_tools(mock_mcp)
    find_patterns = mock_mcp._tools["find_patterns"]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"patterns": []}

    with patch("src.mcp_server.features.patterns.pattern_tools.httpx.AsyncClient") as mock_client:
        mock_async_client = AsyncMock()
        mock_async_client.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_async_client

        result = await find_patterns(mock_context, query="very obscure topic")

    data = json.loads(result)
    assert data["success"] is True
    assert data["count"] == 0
    assert data["patterns"] == []


# =====================================================
# FIND PATTERNS — LIST MODE
# =====================================================

@pytest.mark.asyncio
async def test_find_patterns_list_no_filters(mock_mcp, mock_context, mock_pattern):
    """find_patterns with no args hits GET /api/patterns list endpoint."""
    register_pattern_tools(mock_mcp)
    find_patterns = mock_mcp._tools["find_patterns"]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"patterns": [mock_pattern]}

    with patch("src.mcp_server.features.patterns.pattern_tools.httpx.AsyncClient") as mock_client:
        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_async_client

        result = await find_patterns(mock_context)

    data = json.loads(result)
    assert data["success"] is True
    assert data["mode"] == "list"
    assert data["count"] == 1
    assert "embedding" not in data["patterns"][0]

    call_url = mock_async_client.get.call_args[0][0]
    assert call_url.endswith("/api/patterns")


@pytest.mark.asyncio
async def test_find_patterns_list_with_type_filter(mock_mcp, mock_context, mock_pattern):
    """find_patterns list mode passes pattern_type query param."""
    register_pattern_tools(mock_mcp)
    find_patterns = mock_mcp._tools["find_patterns"]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"patterns": [mock_pattern]}

    with patch("src.mcp_server.features.patterns.pattern_tools.httpx.AsyncClient") as mock_client:
        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_async_client

        result = await find_patterns(mock_context, pattern_type="technical")

    data = json.loads(result)
    assert data["success"] is True

    call_params = mock_async_client.get.call_args[1]["params"]
    assert call_params["pattern_type"] == "technical"


@pytest.mark.asyncio
async def test_find_patterns_list_with_domain_filter(mock_mcp, mock_context, mock_pattern):
    """find_patterns list mode passes domain query param."""
    register_pattern_tools(mock_mcp)
    find_patterns = mock_mcp._tools["find_patterns"]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"patterns": [mock_pattern]}

    with patch("src.mcp_server.features.patterns.pattern_tools.httpx.AsyncClient") as mock_client:
        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_async_client

        result = await find_patterns(mock_context, domain="database")

    data = json.loads(result)
    assert data["success"] is True

    call_params = mock_async_client.get.call_args[1]["params"]
    assert call_params["domain"] == "database"


@pytest.mark.asyncio
async def test_find_patterns_list_http_error(mock_mcp, mock_context):
    """find_patterns list returns error on non-200 response."""
    register_pattern_tools(mock_mcp)
    find_patterns = mock_mcp._tools["find_patterns"]

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal server error"

    with patch("src.mcp_server.features.patterns.pattern_tools.httpx.AsyncClient") as mock_client:
        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_async_client

        result = await find_patterns(mock_context)

    data = json.loads(result)
    assert data["success"] is False
    assert "error" in data


@pytest.mark.asyncio
async def test_find_patterns_handles_exception(mock_mcp, mock_context):
    """find_patterns returns error JSON on unexpected exception."""
    register_pattern_tools(mock_mcp)
    find_patterns = mock_mcp._tools["find_patterns"]

    with patch("src.mcp_server.features.patterns.pattern_tools.httpx.AsyncClient") as mock_client:
        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = Exception("Connection refused")
        mock_client.return_value.__aenter__.return_value = mock_async_client

        result = await find_patterns(mock_context)

    data = json.loads(result)
    assert data["success"] is False
    assert "error" in data


# =====================================================
# MANAGE PATTERN — HARVEST ACTION
# =====================================================

@pytest.mark.asyncio
async def test_manage_pattern_harvest_success(mock_mcp, mock_context, mock_pattern):
    """manage_pattern harvest posts to POST /api/patterns."""
    register_pattern_tools(mock_mcp)
    manage_pattern = mock_mcp._tools["manage_pattern"]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"pattern": mock_pattern}

    with patch("src.mcp_server.features.patterns.pattern_tools.httpx.AsyncClient") as mock_client:
        mock_async_client = AsyncMock()
        mock_async_client.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_async_client

        result = await manage_pattern(
            mock_context,
            action="harvest",
            pattern_type="technical",
            domain="database",
            description="Index frequently queried columns for performance",
            action_text="Create B-tree index on foreign keys",
            outcome="60-80% query time reduction",
            created_by="claude",
        )

    data = json.loads(result)
    assert data["success"] is True
    assert "pattern" in data
    assert "embedding" not in data["pattern"]

    call_url = mock_async_client.post.call_args[0][0]
    assert call_url.endswith("/api/patterns")

    sent_data = mock_async_client.post.call_args[1]["json"]
    assert sent_data["pattern_type"] == "technical"
    assert sent_data["domain"] == "database"
    assert sent_data["action"] == "Create B-tree index on foreign keys"
    assert sent_data["created_by"] == "claude"


@pytest.mark.asyncio
async def test_manage_pattern_harvest_missing_required_fields(mock_mcp, mock_context):
    """manage_pattern harvest returns validation error when required fields missing."""
    register_pattern_tools(mock_mcp)
    manage_pattern = mock_mcp._tools["manage_pattern"]

    result = await manage_pattern(
        mock_context,
        action="harvest",
        pattern_type="technical",
        # missing: domain, description, action_text
    )

    data = json.loads(result)
    assert data["success"] is False
    assert "harvest requires" in data["error"]


@pytest.mark.asyncio
async def test_manage_pattern_harvest_http_error(mock_mcp, mock_context):
    """manage_pattern harvest returns error on non-200 from API."""
    register_pattern_tools(mock_mcp)
    manage_pattern = mock_mcp._tools["manage_pattern"]

    mock_response = MagicMock()
    mock_response.status_code = 422
    mock_response.text = "Validation error"

    with patch("src.mcp_server.features.patterns.pattern_tools.httpx.AsyncClient") as mock_client:
        mock_async_client = AsyncMock()
        mock_async_client.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_async_client

        result = await manage_pattern(
            mock_context,
            action="harvest",
            pattern_type="technical",
            domain="database",
            description="Test",
            action_text="Test action",
        )

    data = json.loads(result)
    assert data["success"] is False
    assert "error" in data


# =====================================================
# MANAGE PATTERN — RECORD OBSERVATION ACTION
# =====================================================

@pytest.mark.asyncio
async def test_manage_pattern_record_observation_success(mock_mcp, mock_context):
    """manage_pattern record_observation posts to POST /api/patterns/observations."""
    register_pattern_tools(mock_mcp)
    manage_pattern = mock_mcp._tools["manage_pattern"]

    pattern_id = str(uuid4())
    mock_observation = {
        "id": str(uuid4()),
        "pattern_id": pattern_id,
        "success_rating": 5,
        "feedback": "Worked perfectly",
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"observation": mock_observation}

    with patch("src.mcp_server.features.patterns.pattern_tools.httpx.AsyncClient") as mock_client:
        mock_async_client = AsyncMock()
        mock_async_client.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_async_client

        result = await manage_pattern(
            mock_context,
            action="record_observation",
            pattern_id=pattern_id,
            success_rating=5,
            feedback="Worked perfectly",
        )

    data = json.loads(result)
    assert data["success"] is True
    assert "observation" in data
    assert data["observation"]["success_rating"] == 5

    call_url = mock_async_client.post.call_args[0][0]
    assert "/api/patterns/observations" in call_url

    sent_data = mock_async_client.post.call_args[1]["json"]
    assert sent_data["pattern_id"] == pattern_id
    assert sent_data["success_rating"] == 5
    assert sent_data["feedback"] == "Worked perfectly"


@pytest.mark.asyncio
async def test_manage_pattern_record_observation_missing_pattern_id(mock_mcp, mock_context):
    """manage_pattern record_observation requires pattern_id."""
    register_pattern_tools(mock_mcp)
    manage_pattern = mock_mcp._tools["manage_pattern"]

    result = await manage_pattern(
        mock_context,
        action="record_observation",
        success_rating=4,
    )

    data = json.loads(result)
    assert data["success"] is False
    assert "record_observation requires" in data["error"]


@pytest.mark.asyncio
async def test_manage_pattern_record_observation_with_session(mock_mcp, mock_context):
    """manage_pattern record_observation includes session_id when provided."""
    register_pattern_tools(mock_mcp)
    manage_pattern = mock_mcp._tools["manage_pattern"]

    pattern_id = str(uuid4())
    session_id = str(uuid4())

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "observation": {"id": str(uuid4()), "pattern_id": pattern_id}
    }

    with patch("src.mcp_server.features.patterns.pattern_tools.httpx.AsyncClient") as mock_client:
        mock_async_client = AsyncMock()
        mock_async_client.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_async_client

        await manage_pattern(
            mock_context,
            action="record_observation",
            pattern_id=pattern_id,
            session_id=session_id,
            success_rating=3,
        )

    sent_data = mock_async_client.post.call_args[1]["json"]
    assert sent_data["session_id"] == session_id


@pytest.mark.asyncio
async def test_manage_pattern_record_observation_http_error(mock_mcp, mock_context):
    """manage_pattern record_observation returns error on non-200 response."""
    register_pattern_tools(mock_mcp)
    manage_pattern = mock_mcp._tools["manage_pattern"]

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Pattern not found"

    with patch("src.mcp_server.features.patterns.pattern_tools.httpx.AsyncClient") as mock_client:
        mock_async_client = AsyncMock()
        mock_async_client.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_async_client

        result = await manage_pattern(
            mock_context,
            action="record_observation",
            pattern_id=str(uuid4()),
        )

    data = json.loads(result)
    assert data["success"] is False
    assert "error" in data


# =====================================================
# MANAGE PATTERN — INVALID ACTION
# =====================================================

@pytest.mark.asyncio
async def test_manage_pattern_invalid_action(mock_mcp, mock_context):
    """manage_pattern with unknown action returns descriptive error."""
    register_pattern_tools(mock_mcp)
    manage_pattern = mock_mcp._tools["manage_pattern"]

    result = await manage_pattern(mock_context, action="destroy")

    data = json.loads(result)
    assert data["success"] is False
    assert "destroy" in data["error"]
    assert "harvest" in data["error"]
    assert "record_observation" in data["error"]


@pytest.mark.asyncio
async def test_manage_pattern_handles_exception(mock_mcp, mock_context):
    """manage_pattern returns error JSON on unexpected exception."""
    register_pattern_tools(mock_mcp)
    manage_pattern = mock_mcp._tools["manage_pattern"]

    with patch("src.mcp_server.features.patterns.pattern_tools.httpx.AsyncClient") as mock_client:
        mock_async_client = AsyncMock()
        mock_async_client.post.side_effect = Exception("Network error")
        mock_client.return_value.__aenter__.return_value = mock_async_client

        result = await manage_pattern(
            mock_context,
            action="harvest",
            pattern_type="technical",
            domain="database",
            description="Test",
            action_text="Test action",
        )

    data = json.loads(result)
    assert data["success"] is False
    assert "error" in data
