#!/bin/bash
# Track Claude Code sessions in Archon
# Usage: ./track-claude-session.sh start "Working on HVAC project"
# Usage: ./track-claude-session.sh end <session-id>

ARCHON_API="http://localhost:8181/api"
SESSION_FILE="/tmp/claude-session-id.txt"

case "$1" in
  start)
    SUMMARY="${2:-Claude Code session}"

    # Create session
    RESPONSE=$(curl -s -X POST "${ARCHON_API}/sessions" \
      -H "Content-Type: application/json" \
      -d "{
        \"agent\": \"claude\",
        \"context\": {
          \"tool\": \"claude-code\",
          \"working_on\": \"${SUMMARY}\"
        }
      }")

    # Extract session ID
    SESSION_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

    if [ -n "$SESSION_ID" ]; then
      echo "$SESSION_ID" > "$SESSION_FILE"
      echo "✅ Session started: $SESSION_ID"
      echo "📝 Summary: $SUMMARY"
      echo ""
      echo "To end this session, run:"
      echo "  ./track-claude-session.sh end $SESSION_ID"
    else
      echo "❌ Failed to start session"
      echo "$RESPONSE"
      exit 1
    fi
    ;;

  end)
    SESSION_ID="${2}"

    if [ -z "$SESSION_ID" ] && [ -f "$SESSION_FILE" ]; then
      SESSION_ID=$(cat "$SESSION_FILE")
    fi

    if [ -z "$SESSION_ID" ]; then
      echo "❌ No session ID provided or found"
      exit 1
    fi

    SUMMARY="${3:-Session completed}"

    # End session
    RESPONSE=$(curl -s -X POST "${ARCHON_API}/sessions/${SESSION_ID}/end" \
      -H "Content-Type: application/json" \
      -d "{
        \"summary\": \"${SUMMARY}\"
      }")

    echo "✅ Session ended: $SESSION_ID"
    rm -f "$SESSION_FILE"
    ;;

  log)
    SESSION_ID="${2}"

    if [ -z "$SESSION_ID" ] && [ -f "$SESSION_FILE" ]; then
      SESSION_ID=$(cat "$SESSION_FILE")
    fi

    if [ -z "$SESSION_ID" ]; then
      echo "❌ No session ID provided or found"
      exit 1
    fi

    EVENT_TYPE="${3:-task}"
    EVENT_DATA="${4:-Event logged}"

    # Log event
    curl -s -X POST "${ARCHON_API}/sessions/events" \
      -H "Content-Type: application/json" \
      -d "{
        \"session_id\": \"${SESSION_ID}\",
        \"event_type\": \"${EVENT_TYPE}\",
        \"event_data\": {
          \"description\": \"${EVENT_DATA}\"
        }
      }" > /dev/null

    echo "📝 Event logged to session: $SESSION_ID"
    ;;

  *)
    echo "Usage:"
    echo "  Start session: $0 start \"Working on feature X\""
    echo "  End session:   $0 end [session-id] [\"Summary\"]"
    echo "  Log event:     $0 log [session-id] [event-type] [\"Event description\"]"
    exit 1
    ;;
esac
