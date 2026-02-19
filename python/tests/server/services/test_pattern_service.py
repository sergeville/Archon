"""
Unit tests for pattern_service.py
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from src.server.services.pattern_service import PatternService, get_pattern_service


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the singleton between tests."""
    import src.server.services.pattern_service as ps_module
    original = ps_module._pattern_service
    yield
    ps_module._pattern_service = original


@pytest.fixture
def pattern_service():
    """Create a fresh PatternService instance with mocked dependencies."""
    with patch("src.server.services.pattern_service.get_supabase_client"), \
         patch("src.server.services.pattern_service.get_embedding_service"):
        service = PatternService()
        return service


@pytest.fixture
def mock_pattern_data():
    """Mock pattern data matching archon_patterns schema."""
    return {
        "id": str(uuid4()),
        "pattern_type": "technical",
        "domain": "database",
        "description": "Query optimization via indexing",
        "action": "Add B-tree index on frequently queried columns",
        "outcome": "60-80% query time reduction",
        "context": {"technology": "PostgreSQL"},
        "embedding": [0.1] * 1536,
        "metadata": {"confidence_score": 0.5, "applications": 0, "success_rate": 0.0},
        "created_by": "claude",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def mock_observation_data():
    """Mock observation data matching archon_pattern_observations schema."""
    return {
        "id": str(uuid4()),
        "pattern_id": str(uuid4()),
        "session_id": None,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "success_rating": 4,
        "feedback": "Worked well",
        "metadata": {},
    }


# =====================================================
# HARVEST PATTERN TESTS
# =====================================================

@pytest.mark.asyncio
async def test_harvest_pattern_success(pattern_service, mock_pattern_data):
    """Test successful pattern creation with embedding."""
    pattern_service.embedding_service.generate_embedding = AsyncMock(
        return_value=[0.1] * 1536
    )

    mock_response = MagicMock()
    mock_response.data = [mock_pattern_data]
    pattern_service.supabase.table.return_value.insert.return_value.execute.return_value = mock_response

    result = await pattern_service.harvest_pattern(
        pattern_type="technical",
        domain="database",
        description="Query optimization via indexing",
        action="Add B-tree index on frequently queried columns",
        outcome="60-80% query time reduction",
        context={"technology": "PostgreSQL"},
        created_by="claude"
    )

    assert result["pattern_type"] == "technical"
    assert result["domain"] == "database"
    pattern_service.supabase.table.assert_called_with("archon_patterns")
    pattern_service.embedding_service.generate_embedding.assert_called_once()


@pytest.mark.asyncio
async def test_harvest_pattern_without_outcome(pattern_service, mock_pattern_data):
    """Test pattern creation without optional fields."""
    mock_pattern_data["outcome"] = None
    mock_pattern_data["context"] = {}

    pattern_service.embedding_service.generate_embedding = AsyncMock(
        return_value=[0.1] * 1536
    )

    mock_response = MagicMock()
    mock_response.data = [mock_pattern_data]
    pattern_service.supabase.table.return_value.insert.return_value.execute.return_value = mock_response

    result = await pattern_service.harvest_pattern(
        pattern_type="process",
        domain="development",
        description="Breaking tasks into subtasks",
        action="Decompose into 5-10 actionable items",
    )

    assert result is not None
    insert_call = pattern_service.supabase.table.return_value.insert.call_args[0][0]
    assert insert_call["outcome"] is None
    assert insert_call["context"] == {}


@pytest.mark.asyncio
async def test_harvest_pattern_embedding_failure_still_saves(pattern_service, mock_pattern_data):
    """Test that pattern is saved even when embedding generation fails."""
    pattern_service.embedding_service.generate_embedding = AsyncMock(
        return_value=None  # No embedding
    )

    mock_response = MagicMock()
    mock_response.data = [mock_pattern_data]
    pattern_service.supabase.table.return_value.insert.return_value.execute.return_value = mock_response

    result = await pattern_service.harvest_pattern(
        pattern_type="success",
        domain="management",
        description="Daily standups improve coordination",
        action="Hold 15-minute daily sync"
    )

    assert result is not None
    insert_call = pattern_service.supabase.table.return_value.insert.call_args[0][0]
    assert "embedding" not in insert_call


@pytest.mark.asyncio
async def test_harvest_pattern_database_error(pattern_service):
    """Test that database errors propagate correctly."""
    pattern_service.embedding_service.generate_embedding = AsyncMock(
        return_value=[0.1] * 1536
    )
    pattern_service.supabase.table.return_value.insert.return_value.execute.side_effect = Exception(
        "Database connection failed"
    )

    with pytest.raises(Exception, match="Database connection failed"):
        await pattern_service.harvest_pattern(
            pattern_type="technical",
            domain="database",
            description="Test pattern",
            action="Test action"
        )


@pytest.mark.asyncio
async def test_harvest_pattern_no_data_returned(pattern_service):
    """Test that empty response raises exception."""
    pattern_service.embedding_service.generate_embedding = AsyncMock(
        return_value=[0.1] * 1536
    )

    mock_response = MagicMock()
    mock_response.data = []
    pattern_service.supabase.table.return_value.insert.return_value.execute.return_value = mock_response

    with pytest.raises(Exception, match="Pattern creation returned no data"):
        await pattern_service.harvest_pattern(
            pattern_type="technical",
            domain="database",
            description="Test",
            action="Test"
        )


# =====================================================
# RECORD OBSERVATION TESTS
# =====================================================

@pytest.mark.asyncio
async def test_record_observation_success(pattern_service, mock_observation_data):
    """Test successful observation recording."""
    pattern_id = uuid4()
    mock_observation_data["pattern_id"] = str(pattern_id)

    mock_response = MagicMock()
    mock_response.data = [mock_observation_data]
    pattern_service.supabase.table.return_value.insert.return_value.execute.return_value = mock_response

    result = await pattern_service.record_observation(
        pattern_id=pattern_id,
        success_rating=4,
        feedback="Worked well"
    )

    assert result["success_rating"] == 4
    assert result["feedback"] == "Worked well"
    pattern_service.supabase.table.assert_called_with("archon_pattern_observations")


@pytest.mark.asyncio
async def test_record_observation_with_session(pattern_service, mock_observation_data):
    """Test observation recording linked to a session."""
    pattern_id = uuid4()
    session_id = uuid4()
    mock_observation_data["session_id"] = str(session_id)

    mock_response = MagicMock()
    mock_response.data = [mock_observation_data]
    pattern_service.supabase.table.return_value.insert.return_value.execute.return_value = mock_response

    await pattern_service.record_observation(
        pattern_id=pattern_id,
        session_id=session_id,
        success_rating=5
    )

    insert_call = pattern_service.supabase.table.return_value.insert.call_args[0][0]
    assert insert_call["session_id"] == str(session_id)


@pytest.mark.asyncio
async def test_record_observation_without_session(pattern_service, mock_observation_data):
    """Test observation without session_id excludes it from insert."""
    pattern_id = uuid4()

    mock_response = MagicMock()
    mock_response.data = [mock_observation_data]
    pattern_service.supabase.table.return_value.insert.return_value.execute.return_value = mock_response

    await pattern_service.record_observation(pattern_id=pattern_id)

    insert_call = pattern_service.supabase.table.return_value.insert.call_args[0][0]
    assert "session_id" not in insert_call


@pytest.mark.asyncio
async def test_record_observation_database_error(pattern_service):
    """Test that database errors propagate from observation recording."""
    pattern_service.supabase.table.return_value.insert.return_value.execute.side_effect = Exception(
        "Foreign key violation"
    )

    with pytest.raises(Exception, match="Foreign key violation"):
        await pattern_service.record_observation(pattern_id=uuid4(), success_rating=3)


# =====================================================
# SEARCH PATTERNS TESTS
# =====================================================

@pytest.mark.asyncio
async def test_search_patterns_success(pattern_service):
    """Test successful semantic pattern search."""
    mock_results = [
        {
            "id": str(uuid4()),
            "pattern_type": "technical",
            "domain": "database",
            "description": "Database indexing for performance",
            "action": "Create indexes",
            "similarity": 0.92,
        },
        {
            "id": str(uuid4()),
            "pattern_type": "technical",
            "domain": "database",
            "description": "Query caching strategy",
            "action": "Cache frequent queries",
            "similarity": 0.81,
        },
    ]

    pattern_service.embedding_service.generate_embedding = AsyncMock(
        return_value=[0.1] * 1536
    )

    mock_response = MagicMock()
    mock_response.data = mock_results
    pattern_service.supabase.rpc.return_value.execute.return_value = mock_response

    results = await pattern_service.search_patterns(
        query="optimize database queries",
        limit=10,
        threshold=0.7
    )

    assert len(results) == 2
    assert results[0]["similarity"] == 0.92
    pattern_service.supabase.rpc.assert_called_with(
        "search_patterns_semantic",
        {
            "p_query_embedding": [0.1] * 1536,
            "p_limit": 10,
            "p_threshold": 0.7,
        }
    )


@pytest.mark.asyncio
async def test_search_patterns_with_domain_filter(pattern_service):
    """Test that domain filter is applied to search results."""
    mock_results = [
        {"id": str(uuid4()), "domain": "database", "similarity": 0.9},
        {"id": str(uuid4()), "domain": "api", "similarity": 0.85},
    ]

    pattern_service.embedding_service.generate_embedding = AsyncMock(
        return_value=[0.1] * 1536
    )

    mock_response = MagicMock()
    mock_response.data = mock_results
    pattern_service.supabase.rpc.return_value.execute.return_value = mock_response

    results = await pattern_service.search_patterns(
        query="performance optimization",
        domain="database"
    )

    assert len(results) == 1
    assert results[0]["domain"] == "database"


@pytest.mark.asyncio
async def test_search_patterns_no_embedding(pattern_service):
    """Test that missing embedding returns empty list."""
    pattern_service.embedding_service.generate_embedding = AsyncMock(return_value=None)

    results = await pattern_service.search_patterns(query="test query")

    assert results == []
    pattern_service.supabase.rpc.assert_not_called()


@pytest.mark.asyncio
async def test_search_patterns_empty_results(pattern_service):
    """Test search returning no matches."""
    pattern_service.embedding_service.generate_embedding = AsyncMock(
        return_value=[0.1] * 1536
    )

    mock_response = MagicMock()
    mock_response.data = []
    pattern_service.supabase.rpc.return_value.execute.return_value = mock_response

    results = await pattern_service.search_patterns(query="very obscure topic")

    assert results == []


# =====================================================
# GET PATTERN TESTS
# =====================================================

@pytest.mark.asyncio
async def test_get_pattern_success(pattern_service, mock_pattern_data):
    """Test retrieving a pattern by ID with observation stats."""
    pattern_id = UUID(mock_pattern_data["id"])

    mock_select_response = MagicMock()
    mock_select_response.data = [mock_pattern_data]

    mock_obs_response = MagicMock()
    mock_obs_response.data = [
        {"success_rating": 5},
        {"success_rating": 4},
        {"success_rating": 3},
    ]

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.execute.return_value = mock_select_response

    mock_obs_query = MagicMock()
    mock_obs_query.eq.return_value = mock_obs_query
    mock_obs_query.execute.return_value = mock_obs_response

    # First call returns pattern, second returns observations
    pattern_service.supabase.table.return_value.select.side_effect = [
        mock_query,
        mock_obs_query,
    ]

    result = await pattern_service.get_pattern(pattern_id)

    assert result is not None
    assert result["id"] == mock_pattern_data["id"]
    assert result["observation_count"] == 3
    assert result["average_rating"] == 4.0


@pytest.mark.asyncio
async def test_get_pattern_not_found(pattern_service):
    """Test that missing pattern returns None."""
    mock_response = MagicMock()
    mock_response.data = []

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.execute.return_value = mock_response

    pattern_service.supabase.table.return_value.select.return_value = mock_query

    result = await pattern_service.get_pattern(uuid4())

    assert result is None


@pytest.mark.asyncio
async def test_get_pattern_no_observations(pattern_service, mock_pattern_data):
    """Test pattern with zero observations."""
    pattern_id = UUID(mock_pattern_data["id"])

    mock_pattern_response = MagicMock()
    mock_pattern_response.data = [mock_pattern_data]

    mock_obs_response = MagicMock()
    mock_obs_response.data = []

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query

    mock_query.execute.side_effect = [mock_pattern_response, mock_obs_response]
    pattern_service.supabase.table.return_value.select.return_value = mock_query

    result = await pattern_service.get_pattern(pattern_id)

    assert result["observation_count"] == 0
    assert result["average_rating"] is None


# =====================================================
# GET PATTERN STATS TESTS
# =====================================================

@pytest.mark.asyncio
async def test_get_pattern_stats_success(pattern_service):
    """Test retrieving global pattern statistics."""
    mock_patterns = [
        {"pattern_type": "technical"},
        {"pattern_type": "technical"},
        {"pattern_type": "success"},
        {"pattern_type": "process"},
    ]

    mock_patterns_resp = MagicMock()
    mock_patterns_resp.count = 4
    mock_patterns_resp.data = mock_patterns

    mock_obs_resp = MagicMock()
    mock_obs_resp.count = 12

    mock_query = MagicMock()
    mock_query.select.return_value = mock_query
    mock_query.execute.side_effect = [mock_patterns_resp, mock_obs_resp]

    pattern_service.supabase.table.return_value = mock_query

    result = await pattern_service.get_pattern_stats()

    assert result["total_patterns"] == 4
    assert result["total_observations"] == 12
    assert result["by_type"]["technical"] == 2
    assert result["by_type"]["success"] == 1
    assert result["by_type"]["process"] == 1


@pytest.mark.asyncio
async def test_get_pattern_stats_database_error(pattern_service):
    """Test that stats returns error dict on database failure."""
    pattern_service.supabase.table.return_value.select.return_value.execute.side_effect = Exception(
        "DB error"
    )

    result = await pattern_service.get_pattern_stats()

    assert "error" in result


# =====================================================
# LIST PATTERNS TESTS
# =====================================================

@pytest.mark.asyncio
async def test_list_patterns_no_filters(pattern_service, mock_pattern_data):
    """Test listing all patterns without filters."""
    mock_response = MagicMock()
    mock_response.data = [mock_pattern_data]

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.execute.return_value = mock_response
    pattern_service.supabase.table.return_value.select.return_value = mock_query

    result = await pattern_service.list_patterns()

    assert len(result) == 1
    assert result[0]["pattern_type"] == "technical"
    mock_query.order.assert_called_once_with("created_at", desc=True)
    mock_query.limit.assert_called_once_with(50)


@pytest.mark.asyncio
async def test_list_patterns_with_type_filter(pattern_service, mock_pattern_data):
    """Test listing patterns filtered by type."""
    mock_response = MagicMock()
    mock_response.data = [mock_pattern_data]

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.execute.return_value = mock_response
    pattern_service.supabase.table.return_value.select.return_value = mock_query

    result = await pattern_service.list_patterns(pattern_type="technical")

    assert len(result) == 1
    mock_query.eq.assert_any_call("pattern_type", "technical")


@pytest.mark.asyncio
async def test_list_patterns_with_domain_filter(pattern_service, mock_pattern_data):
    """Test listing patterns filtered by domain."""
    mock_response = MagicMock()
    mock_response.data = [mock_pattern_data]

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.execute.return_value = mock_response
    pattern_service.supabase.table.return_value.select.return_value = mock_query

    result = await pattern_service.list_patterns(domain="database")

    assert len(result) == 1
    mock_query.eq.assert_any_call("domain", "database")


@pytest.mark.asyncio
async def test_list_patterns_empty(pattern_service):
    """Test listing when no patterns exist."""
    mock_response = MagicMock()
    mock_response.data = []

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.execute.return_value = mock_response
    pattern_service.supabase.table.return_value.select.return_value = mock_query

    result = await pattern_service.list_patterns()

    assert result == []


@pytest.mark.asyncio
async def test_list_patterns_custom_limit(pattern_service):
    """Test listing with custom limit."""
    mock_response = MagicMock()
    mock_response.data = []

    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.execute.return_value = mock_response
    pattern_service.supabase.table.return_value.select.return_value = mock_query

    await pattern_service.list_patterns(limit=5)

    mock_query.limit.assert_called_once_with(5)


@pytest.mark.asyncio
async def test_list_patterns_database_error(pattern_service):
    """Test that database errors propagate from list_patterns."""
    mock_query = MagicMock()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.execute.side_effect = Exception("Connection timeout")
    pattern_service.supabase.table.return_value.select.return_value = mock_query

    with pytest.raises(Exception, match="Connection timeout"):
        await pattern_service.list_patterns()


# =====================================================
# EXTRACT PATTERNS FROM SESSION TESTS
# =====================================================

@pytest.mark.asyncio
async def test_extract_patterns_from_session_no_session(pattern_service):
    """Returns empty list when session does not exist."""
    mock_session_service = AsyncMock()
    mock_session_service.get_session.return_value = None

    with patch("src.server.services.session_service.get_session_service", return_value=mock_session_service), \
         patch("src.agents.features.pattern_extractor.extract_patterns"):
        result = await pattern_service.extract_patterns_from_session(uuid4())

    assert result == []
    mock_session_service.get_session.assert_called_once()


@pytest.mark.asyncio
async def test_extract_patterns_from_session_no_events(pattern_service):
    """Returns empty list when session has no events and AI finds no patterns."""
    from src.agents.features.pattern_extractor import ExtractedPatterns

    mock_session_service = AsyncMock()
    mock_session_service.get_session.return_value = {
        "id": str(uuid4()),
        "agent": "claude",
        "events": [],
        "summary": "",
    }

    mock_extracted = ExtractedPatterns(patterns=[], rationale="No events to analyze")

    with patch("src.server.services.session_service.get_session_service", return_value=mock_session_service), \
         patch("src.agents.features.pattern_extractor.extract_patterns", new=AsyncMock(return_value=mock_extracted)):
        result = await pattern_service.extract_patterns_from_session(uuid4())

    assert result == []


@pytest.mark.asyncio
async def test_extract_patterns_from_session_stores_high_confidence(pattern_service, mock_pattern_data):
    """High-confidence candidates are harvested and returned."""
    from src.agents.features.pattern_extractor import ExtractedPatterns, PatternCandidate

    session_id = uuid4()
    mock_session_service = AsyncMock()
    mock_session_service.get_session.return_value = {
        "id": str(session_id),
        "agent": "claude",
        "events": [{"event_type": "task_completed", "created_at": "2026-02-19T10:00:00Z", "event_data": {}}],
        "summary": "Completed database migration successfully",
    }

    candidate = PatternCandidate(
        pattern_type="technical",
        domain="database",
        description="Run migrations in transaction to allow rollback",
        action="Wrap ALTER TABLE statements in BEGIN/COMMIT block",
        outcome="Zero-downtime schema changes",
        confidence=0.9,
    )
    mock_extracted = ExtractedPatterns(
        patterns=[candidate],
        rationale="Database migration pattern identified",
    )

    mock_response = MagicMock()
    mock_response.data = [mock_pattern_data]
    pattern_service.supabase.table.return_value.insert.return_value.execute.return_value = mock_response
    pattern_service.embedding_service.generate_embedding = AsyncMock(return_value=[0.1] * 1536)

    with patch("src.server.services.session_service.get_session_service", return_value=mock_session_service), \
         patch("src.agents.features.pattern_extractor.extract_patterns", new=AsyncMock(return_value=mock_extracted)):
        result = await pattern_service.extract_patterns_from_session(session_id)

    assert len(result) == 1
    insert_call = pattern_service.supabase.table.return_value.insert.call_args[0][0]
    assert str(session_id) in insert_call["context"]["source_session_id"]
    assert insert_call["created_by"] == "pattern_extractor"


@pytest.mark.asyncio
async def test_extract_patterns_from_session_skips_low_confidence(pattern_service):
    """Candidates with confidence < 0.6 are skipped and not stored."""
    from src.agents.features.pattern_extractor import ExtractedPatterns, PatternCandidate

    mock_session_service = AsyncMock()
    mock_session_service.get_session.return_value = {
        "id": str(uuid4()),
        "agent": "claude",
        "events": [{"event_type": "file_edited", "created_at": "", "event_data": {}}],
        "summary": "",
    }

    low_confidence = PatternCandidate(
        pattern_type="process",
        domain="development",
        description="Vague pattern with low confidence",
        action="Do something",
        confidence=0.4,
    )
    mock_extracted = ExtractedPatterns(
        patterns=[low_confidence],
        rationale="Low signal session",
    )

    with patch("src.server.services.session_service.get_session_service", return_value=mock_session_service), \
         patch("src.agents.features.pattern_extractor.extract_patterns", new=AsyncMock(return_value=mock_extracted)):
        result = await pattern_service.extract_patterns_from_session(uuid4())

    assert result == []
    pattern_service.supabase.table.assert_not_called()


# =====================================================
# SINGLETON TESTS
# =====================================================

def test_get_pattern_service_singleton():
    """Test that get_pattern_service returns the same instance."""
    import src.server.services.pattern_service as ps_module
    ps_module._pattern_service = None  # Reset for clean test

    with patch("src.server.services.pattern_service.get_supabase_client"), \
         patch("src.server.services.pattern_service.get_embedding_service"):
        service1 = get_pattern_service()
        service2 = get_pattern_service()

    assert service1 is service2


def test_get_pattern_service_returns_pattern_service_instance():
    """Test that singleton returns a PatternService instance."""
    import src.server.services.pattern_service as ps_module
    ps_module._pattern_service = None

    with patch("src.server.services.pattern_service.get_supabase_client"), \
         patch("src.server.services.pattern_service.get_embedding_service"):
        service = get_pattern_service()

    assert isinstance(service, PatternService)
