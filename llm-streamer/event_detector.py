"""
Event Detector for Archon Log Collector

Parses Docker log lines and detects structured events for whiteboard integration.
Publishes to Redis channels: events:task, events:session, events:system
"""

import re
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any


class EventDetector:
    """Detects and structures events from Docker log lines"""

    def __init__(self):
        """Initialize event patterns"""
        self.patterns = self._build_patterns()

    def _build_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Build regex patterns for event detection"""
        return {
            # Task events (from our EventPublisher logs)
            "task_created": {
                "pattern": re.compile(r"Published task\.created event for task ([\w-]+)"),
                "channel": "events:task",
                "event_type": "task.created",
                "extract": lambda m: {"task_id": m.group(1)}
            },
            "task_status_changed": {
                "pattern": re.compile(r"Published task\.status_changed event for task ([\w-]+)"),
                "channel": "events:task",
                "event_type": "task.status_changed",
                "extract": lambda m: {"task_id": m.group(1)}
            },
            "task_assigned": {
                "pattern": re.compile(r"Published task\.assigned event for task ([\w-]+)"),
                "channel": "events:task",
                "event_type": "task.assigned",
                "extract": lambda m: {"task_id": m.group(1)}
            },

            # Session events
            "session_started": {
                "pattern": re.compile(r"Published session\.started event for session ([\w-]+)"),
                "channel": "events:session",
                "event_type": "session.started",
                "extract": lambda m: {"session_id": m.group(1)}
            },
            "session_ended": {
                "pattern": re.compile(r"Published session\.ended event for session ([\w-]+)"),
                "channel": "events:session",
                "event_type": "session.ended",
                "extract": lambda m: {"session_id": m.group(1)}
            },

            # Whiteboard updates (from EventListenerService)
            "whiteboard_task_added": {
                "pattern": re.compile(r"Added task ([\w-]+) to whiteboard"),
                "channel": "events:system",
                "event_type": "whiteboard.task_added",
                "extract": lambda m: {"task_id": m.group(1)}
            },
            "whiteboard_task_updated": {
                "pattern": re.compile(r"Updated task ([\w-]+) on whiteboard: (\w+) → (\w+)"),
                "channel": "events:system",
                "event_type": "whiteboard.task_updated",
                "extract": lambda m: {
                    "task_id": m.group(1),
                    "old_status": m.group(2),
                    "new_status": m.group(3)
                }
            },
            "whiteboard_session_added": {
                "pattern": re.compile(r"Added session ([\w-]+) \((\w+)\) to whiteboard"),
                "channel": "events:system",
                "event_type": "whiteboard.session_added",
                "extract": lambda m: {"session_id": m.group(1), "agent": m.group(2)}
            },
            "whiteboard_session_removed": {
                "pattern": re.compile(r"Removed session ([\w-]+) from whiteboard"),
                "channel": "events:system",
                "event_type": "whiteboard.session_removed",
                "extract": lambda m: {"session_id": m.group(1)}
            },

            # Service health events
            "service_started": {
                "pattern": re.compile(r"([\w-]+) service started successfully"),
                "channel": "events:system",
                "event_type": "service.started",
                "extract": lambda m: {"service_name": m.group(1)}
            },
            "service_stopped": {
                "pattern": re.compile(r"([\w-]+) service stopped"),
                "channel": "events:system",
                "event_type": "service.stopped",
                "extract": lambda m: {"service_name": m.group(1)}
            },

            # Container health
            "backend_started": {
                "pattern": re.compile(r"🎉 Archon backend started successfully!"),
                "channel": "events:system",
                "event_type": "backend.started",
                "extract": lambda m: {}
            },
            "backend_shutdown": {
                "pattern": re.compile(r"🛑 Shutting down Archon backend"),
                "channel": "events:system",
                "event_type": "backend.shutdown",
                "extract": lambda m: {}
            },

            # Error patterns
            "error_occurred": {
                "pattern": re.compile(r"ERROR.*?:\s*(.+)$", re.IGNORECASE),
                "channel": "events:system",
                "event_type": "error.occurred",
                "extract": lambda m: {"error_message": m.group(1).strip()}
            },
            "warning_occurred": {
                "pattern": re.compile(r"WARNING.*?:\s*(.+)$", re.IGNORECASE),
                "channel": "events:system",
                "event_type": "warning.occurred",
                "extract": lambda m: {"warning_message": m.group(1).strip()}
            },

            # Crawl events
            "crawl_started": {
                "pattern": re.compile(r"Starting crawl for URL: (.+)"),
                "channel": "events:system",
                "event_type": "crawl.started",
                "extract": lambda m: {"url": m.group(1).strip()}
            },
            "crawl_completed": {
                "pattern": re.compile(r"Crawl completed for (.+)"),
                "channel": "events:system",
                "event_type": "crawl.completed",
                "extract": lambda m: {"url": m.group(1).strip()}
            },

            # API request patterns
            "api_request": {
                "pattern": re.compile(r"(GET|POST|PUT|DELETE|PATCH)\s+(/api/[\w/]+)"),
                "channel": "events:system",
                "event_type": "api.request",
                "extract": lambda m: {"method": m.group(1), "path": m.group(2)}
            },

            # TodoWrite / Task list operations
            "todo_item_completed": {
                "pattern": re.compile(r"(?:Task|Todo|Item)\s+(?:completed|done|finished):\s*(.+)$", re.IGNORECASE),
                "channel": "events:task",
                "event_type": "task.completed",
                "extract": lambda m: {"description": m.group(1).strip()}
            },
            "todo_item_started": {
                "pattern": re.compile(r"(?:Started|Beginning|Working on)\s+(?:task|todo):\s*(.+)$", re.IGNORECASE),
                "channel": "events:task",
                "event_type": "task.started",
                "extract": lambda m: {"description": m.group(1).strip()}
            },
            "todo_item_added": {
                "pattern": re.compile(r"(?:Added|Created)\s+(?:task|todo):\s*(.+)$", re.IGNORECASE),
                "channel": "events:task",
                "event_type": "task.added",
                "extract": lambda m: {"description": m.group(1).strip()}
            },
            "todos_modified": {
                "pattern": re.compile(r"Todos have been modified successfully"),
                "channel": "events:task",
                "event_type": "task.list_updated",
                "extract": lambda m: {}
            }
        }

    def detect_event(
        self, log_line: str, service_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Detect events from a log line.

        Args:
            log_line: The raw log line from Docker
            service_name: Name of the container (archon-server, archon-mcp, etc.)

        Returns:
            Structured event dict if pattern matched, None otherwise
        """
        # Try each pattern
        for pattern_name, pattern_config in self.patterns.items():
            match = pattern_config["pattern"].search(log_line)
            if match:
                try:
                    # Extract data from match
                    extracted_data = pattern_config["extract"](match)

                    # Build structured event
                    event = {
                        "event_type": pattern_config["event_type"],
                        "entity_type": self._get_entity_type(pattern_config["event_type"]),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "source": service_name,
                        "data": {
                            "log_line": log_line.strip(),
                            **extracted_data
                        }
                    }

                    # Add entity_id if available
                    if "task_id" in extracted_data:
                        event["entity_id"] = extracted_data["task_id"]
                    elif "session_id" in extracted_data:
                        event["entity_id"] = extracted_data["session_id"]
                    elif "service_name" in extracted_data:
                        event["entity_id"] = extracted_data["service_name"]

                    return {
                        "channel": pattern_config["channel"],
                        "event": event
                    }

                except Exception as e:
                    # Pattern matched but extraction failed, skip
                    print(f"⚠️  Event extraction failed for pattern {pattern_name}: {e}")
                    continue

        return None

    def _get_entity_type(self, event_type: str) -> str:
        """Determine entity type from event type"""
        if event_type.startswith("task."):
            return "task"
        elif event_type.startswith("session."):
            return "session"
        elif event_type.startswith("service."):
            return "service"
        elif event_type.startswith("backend."):
            return "backend"
        elif event_type.startswith("whiteboard."):
            return "whiteboard"
        elif event_type.startswith("crawl."):
            return "crawl"
        elif event_type.startswith("api."):
            return "api"
        elif event_type.startswith("error."):
            return "error"
        elif event_type.startswith("warning."):
            return "warning"
        else:
            return "system"

    def should_publish_to_events(self, event_data: Dict[str, Any]) -> bool:
        """
        Determine if an event should be published to events:* channels.

        Some events are too noisy (like API requests) and should only go to logs.
        """
        event_type = event_data["event"]["event_type"]

        # Don't publish API requests to events channels (too noisy)
        if event_type == "api.request":
            return False

        # Don't publish generic warnings unless they're critical
        if event_type == "warning.occurred":
            warning_msg = event_data["event"]["data"].get("warning_message", "")
            # Only publish critical warnings
            if "Could not start" not in warning_msg and "Failed to" not in warning_msg:
                return False

        return True
