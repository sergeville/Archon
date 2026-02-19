"""
Pattern Extraction Agent for Archon

Uses PydanticAI to analyze agent session events and extract reusable patterns.
Identifies recurring sequences of actions, decisions, and outcomes that could
be applied in future sessions.
"""

from typing import Optional

from pydantic import BaseModel, Field
from pydantic_ai import Agent


class PatternCandidate(BaseModel):
    """A single pattern candidate identified from session analysis."""

    pattern_type: str = Field(
        description="Type of pattern: 'success' (worked well), 'failure' (avoid this), "
                    "'technical' (implementation approach), or 'process' (workflow/methodology)"
    )
    domain: str = Field(
        description="Application domain, e.g. 'database', 'api', 'development', 'management', 'testing'"
    )
    description: str = Field(
        description="Clear, reusable description of what the pattern is (1-2 sentences)"
    )
    action: str = Field(
        description="The concrete, reusable action that constitutes the pattern"
    )
    outcome: Optional[str] = Field(
        default=None,
        description="The observed result when this pattern was applied"
    )
    confidence: float = Field(
        description="Confidence that this is a genuinely reusable pattern (0.0-1.0)"
    )


class ExtractedPatterns(BaseModel):
    """Result of pattern extraction from a session."""

    patterns: list[PatternCandidate] = Field(
        description="List of reusable patterns identified in the session. "
                    "Only include patterns with high confidence (>0.6) that are genuinely reusable."
    )
    rationale: str = Field(
        description="Brief explanation of what the session accomplished and why these patterns were selected"
    )


# Initialize the PydanticAI agent
pattern_extractor = Agent(
    "anthropic:claude-sonnet-4-5-20250929",
    output_type=ExtractedPatterns,
    system_prompt="""
    You are a pattern extraction agent for Archon, a multi-agent knowledge management system.

    Your task is to analyze agent session events and identify reusable behavioral and technical patterns.
    Patterns represent proven approaches or known failure modes that can be applied in future sessions.

    Pattern types:
    - "success": An approach that worked well and should be repeated
    - "failure": Something that went wrong and should be avoided
    - "technical": A specific technical implementation approach (e.g., database indexing, API design)
    - "process": A workflow or methodology that was effective (e.g., task decomposition, review steps)

    Rules for good patterns:
    1. Patterns must be REUSABLE — generic enough to apply beyond this specific session
    2. Actions must be CONCRETE — someone reading the pattern should know exactly what to do
    3. Only extract patterns with genuine signal — not every event is a pattern
    4. Prefer fewer high-quality patterns over many vague ones
    5. If a session has no clear reusable patterns, return an empty list

    Do NOT create patterns for:
    - One-off fixes that are too specific to this exact situation
    - Obvious best practices that don't need documenting
    - Events that lack enough context to form a pattern
    """,
)


async def extract_patterns(session: dict, events: list[dict]) -> ExtractedPatterns:
    """
    Analyze session events and extract reusable patterns using AI.

    Args:
        session: Session metadata (agent, project_id, started_at, summary, etc.)
        events: List of session events with event_type, timestamp, and event_data

    Returns:
        ExtractedPatterns with structured candidates ready to be stored
    """
    agent_name = session.get("agent", "Unknown")
    project_id = session.get("project_id")
    summary = session.get("summary", "")
    event_count = len(events)

    # Format events for analysis — mirror the session_summarizer format
    event_lines = []
    for i, event in enumerate(events, 1):
        event_type = event.get("event_type", "unknown")
        timestamp = event.get("created_at") or event.get("timestamp", "")
        data = event.get("event_data") or event.get("data", {})

        if isinstance(data, dict):
            data_summary = ", ".join(f"{k}: {v}" for k, v in data.items() if v)
        else:
            data_summary = str(data)

        event_lines.append(f"{i}. [{event_type}] @ {timestamp}: {data_summary}")

    events_text = "\n".join(event_lines) if event_lines else "No events recorded"

    prompt = f"""
Analyze this agent session and extract reusable patterns:

Agent: {agent_name}
Project ID: {project_id or "None"}
Total Events: {event_count}
Session Summary: {summary or "Not provided"}

Events:
{events_text}

Identify any patterns that are genuinely reusable in future sessions.
Focus on what worked, what failed, and what technical or process approaches were applied.
"""

    result = await pattern_extractor.run(prompt)
    return result.output
