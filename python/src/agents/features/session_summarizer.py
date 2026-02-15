"""
Session Summarization Agent for Archon

Uses PydanticAI to generate structured summaries of agent sessions.
Analyzes session events to extract:
- What was accomplished
- Key decisions made
- Problems encountered
- Next steps suggested
"""

from pydantic import BaseModel, Field
from pydantic_ai import Agent


class SessionSummary(BaseModel):
    """Structured summary of an agent session"""

    summary: str = Field(
        description="Concise overall summary of what happened in this session (2-3 sentences)"
    )
    key_events: list[str] = Field(
        description="List of important events or actions that occurred"
    )
    decisions_made: list[str] = Field(
        description="Key decisions or choices made during the session"
    )
    outcomes: list[str] = Field(
        description="Results, accomplishments, or deliverables from the session"
    )
    next_steps: list[str] = Field(
        description="Suggested next actions or follow-up tasks"
    )


# Initialize the PydanticAI agent
session_summarizer = Agent(
    "openai:gpt-4o-mini",  # Using gpt-4o-mini for cost efficiency
    result_type=SessionSummary,
    system_prompt="""
    You are a session summarization agent for Archon, a multi-agent knowledge management system.

    Your task is to analyze agent session events and create a concise, structured summary.

    Focus on:
    1. What was accomplished (outcomes and deliverables)
    2. Key decisions made during the session
    3. Problems encountered and how they were resolved
    4. Next steps suggested or implied by the work done

    Be concise but specific. Include relevant IDs, file paths, or technical details.
    Use past tense for events and outcomes.
    Use imperative mood for next steps (e.g., "Complete the migration", not "Should complete the migration").

    If a session has very few events or limited information, keep summaries brief but informative.
    """,
)


async def summarize_session(session: dict, events: list[dict]) -> SessionSummary:
    """
    Generate structured summary of a session using AI.

    Args:
        session: Session metadata (agent, project_id, started_at, ended_at, etc.)
        events: List of session events with timestamps, event_type, and data

    Returns:
        SessionSummary with structured analysis of the session
    """
    # Build context for the agent
    agent_name = session.get("agent", "Unknown")
    project_id = session.get("project_id")
    started_at = session.get("started_at", "Unknown")
    ended_at = session.get("ended_at", "Unknown")
    event_count = len(events)

    # Format events for analysis
    event_descriptions = []
    for i, event in enumerate(events, 1):
        event_type = event.get("event_type", "unknown")
        timestamp = event.get("timestamp", "")
        data = event.get("data", {})

        # Extract meaningful info from event data
        if isinstance(data, dict):
            data_summary = ", ".join([f"{k}: {v}" for k, v in data.items() if v])
        else:
            data_summary = str(data)

        event_descriptions.append(
            f"{i}. [{event_type}] @ {timestamp}: {data_summary}"
        )

    events_text = "\n".join(event_descriptions)

    # Create prompt for the agent
    prompt = f"""
Analyze this agent session and create a structured summary:

Agent: {agent_name}
Project ID: {project_id or "None"}
Started: {started_at}
Ended: {ended_at}
Total Events: {event_count}

Events:
{events_text}

Generate a comprehensive summary covering what was accomplished, decisions made, any problems, and next steps.
"""

    # Run the AI agent
    result = await session_summarizer.run(prompt)

    return result.data
