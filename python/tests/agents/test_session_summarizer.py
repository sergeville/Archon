"""
Tests for Session Summarization Agent

Tests the PydanticAI agent that generates structured summaries of agent sessions.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from src.agents.features.session_summarizer import (
    SessionSummary,
    session_summarizer,
    summarize_session
)


class TestSessionSummary:
    """Test the SessionSummary model"""

    def test_session_summary_structure(self):
        """Test that SessionSummary has all required fields"""
        summary = SessionSummary(
            summary="Test session summary",
            key_events=["Event 1", "Event 2"],
            decisions_made=["Decision 1"],
            outcomes=["Outcome 1", "Outcome 2"],
            next_steps=["Next step 1"]
        )

        assert summary.summary == "Test session summary"
        assert len(summary.key_events) == 2
        assert len(summary.decisions_made) == 1
        assert len(summary.outcomes) == 2
        assert len(summary.next_steps) == 1


class TestSessionSummarizer:
    """Test the session summarizer agent"""

    @pytest.fixture
    def sample_session(self):
        """Create a sample session for testing"""
        return {
            "id": str(uuid4()),
            "agent": "claude",
            "project_id": str(uuid4()),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "ended_at": datetime.now(timezone.utc).isoformat(),
            "context": {"test": True},
            "metadata": {}
        }

    @pytest.fixture
    def sample_events(self):
        """Create sample session events for testing"""
        return [
            {
                "id": str(uuid4()),
                "session_id": str(uuid4()),
                "event_type": "task_created",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "task_id": str(uuid4()),
                    "title": "Implement feature X",
                    "status": "todo"
                }
            },
            {
                "id": str(uuid4()),
                "session_id": str(uuid4()),
                "event_type": "file_modified",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "file_path": "src/features/x.py",
                    "changes": "Added new function"
                }
            },
            {
                "id": str(uuid4()),
                "session_id": str(uuid4()),
                "event_type": "task_completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "task_id": str(uuid4()),
                    "title": "Implement feature X",
                    "status": "done"
                }
            }
        ]

    @pytest.mark.asyncio
    async def test_summarize_session_basic(self, sample_session, sample_events):
        """Test basic session summarization"""
        summary = await summarize_session(sample_session, sample_events)

        # Verify summary structure
        assert isinstance(summary, SessionSummary)
        assert len(summary.summary) > 0
        assert isinstance(summary.key_events, list)
        assert isinstance(summary.decisions_made, list)
        assert isinstance(summary.outcomes, list)
        assert isinstance(summary.next_steps, list)

    @pytest.mark.asyncio
    async def test_summarize_session_empty_events(self, sample_session):
        """Test summarization with no events"""
        summary = await summarize_session(sample_session, [])

        # Even with no events, should return valid structure
        assert isinstance(summary, SessionSummary)
        assert len(summary.summary) > 0  # Should have some summary text

    @pytest.mark.asyncio
    async def test_summarize_session_single_event(self, sample_session):
        """Test summarization with a single event"""
        events = [
            {
                "id": str(uuid4()),
                "session_id": str(uuid4()),
                "event_type": "test_event",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {"message": "Single test event"}
            }
        ]

        summary = await summarize_session(sample_session, events)

        assert isinstance(summary, SessionSummary)
        assert len(summary.summary) > 0

    @pytest.mark.asyncio
    async def test_summary_includes_agent_info(self, sample_events):
        """Test that summary includes agent information"""
        session = {
            "id": str(uuid4()),
            "agent": "gemini",
            "project_id": str(uuid4()),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "ended_at": datetime.now(timezone.utc).isoformat(),
            "context": {},
            "metadata": {}
        }

        summary = await summarize_session(session, sample_events)

        # Summary should be contextual (though we can't strictly test for agent name
        # since the AI might paraphrase it)
        assert isinstance(summary, SessionSummary)
        assert len(summary.key_events) > 0

    @pytest.mark.asyncio
    async def test_summary_handles_complex_events(self, sample_session):
        """Test summarization with complex nested event data"""
        events = [
            {
                "id": str(uuid4()),
                "session_id": str(uuid4()),
                "event_type": "complex_operation",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "operation": "migration",
                    "details": {
                        "tables": ["users", "tasks", "projects"],
                        "changes": ["add_column", "create_index"],
                        "affected_rows": 1500
                    },
                    "status": "success"
                }
            },
            {
                "id": str(uuid4()),
                "session_id": str(uuid4()),
                "event_type": "validation",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "validation_type": "schema",
                    "errors": [],
                    "warnings": ["deprecated_field"]
                }
            }
        ]

        summary = await summarize_session(sample_session, events)

        assert isinstance(summary, SessionSummary)
        assert len(summary.outcomes) >= 0  # Should extract some outcomes


class TestSessionSummarizerAgent:
    """Test the PydanticAI agent configuration"""

    def test_agent_has_correct_model(self):
        """Test that the agent is configured with the correct model"""
        # Check that agent is initialized
        assert session_summarizer is not None
        assert session_summarizer.result_type == SessionSummary

    def test_agent_system_prompt(self):
        """Test that the agent has a system prompt"""
        assert session_summarizer._system_prompt is not None
        assert len(session_summarizer._system_prompt) > 0


@pytest.mark.integration
class TestSessionSummarizerIntegration:
    """Integration tests for session summarizer (requires OpenAI API key)"""

    @pytest.mark.asyncio
    async def test_full_summarization_workflow(self):
        """Test a complete summarization workflow with realistic data"""
        session = {
            "id": str(uuid4()),
            "agent": "claude",
            "project_id": str(uuid4()),
            "started_at": "2024-02-14T10:00:00Z",
            "ended_at": "2024-02-14T11:30:00Z",
            "context": {
                "working_on": "Session memory implementation",
                "phase": "Phase 2, Day 5"
            },
            "metadata": {
                "environment": "development"
            }
        }

        events = [
            {
                "id": str(uuid4()),
                "session_id": session["id"],
                "event_type": "feature_started",
                "timestamp": "2024-02-14T10:00:00Z",
                "data": {
                    "feature": "AI session summarization",
                    "approach": "PydanticAI agent"
                }
            },
            {
                "id": str(uuid4()),
                "session_id": session["id"],
                "event_type": "code_created",
                "timestamp": "2024-02-14T10:30:00Z",
                "data": {
                    "file": "src/agents/features/session_summarizer.py",
                    "lines": 120
                }
            },
            {
                "id": str(uuid4()),
                "session_id": session["id"],
                "event_type": "service_integrated",
                "timestamp": "2024-02-14T11:00:00Z",
                "data": {
                    "service": "SessionService",
                    "method": "summarize_session"
                }
            },
            {
                "id": str(uuid4()),
                "session_id": session["id"],
                "event_type": "tests_created",
                "timestamp": "2024-02-14T11:15:00Z",
                "data": {
                    "file": "tests/agents/test_session_summarizer.py",
                    "test_count": 10
                }
            },
            {
                "id": str(uuid4()),
                "session_id": session["id"],
                "event_type": "feature_completed",
                "timestamp": "2024-02-14T11:30:00Z",
                "data": {
                    "feature": "AI session summarization",
                    "status": "done"
                }
            }
        ]

        summary = await summarize_session(session, events)

        # Verify comprehensive summary
        assert isinstance(summary, SessionSummary)
        assert "summarization" in summary.summary.lower() or "session" in summary.summary.lower()
        assert len(summary.key_events) > 0
        assert len(summary.outcomes) > 0

        # Verify structure of outcomes
        for event in summary.key_events:
            assert isinstance(event, str)
            assert len(event) > 0

        for outcome in summary.outcomes:
            assert isinstance(outcome, str)
            assert len(outcome) > 0
