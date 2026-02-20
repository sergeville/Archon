#!/usr/bin/env python3
"""
Test EventDetector pattern matching

Tests various log line patterns to ensure events are detected correctly.
"""

from event_detector import EventDetector


def test_event_detection():
    """Test event detector with sample log lines"""
    detector = EventDetector()

    test_cases = [
        # Task events
        ("2026-02-16 13:32:59 | src.server.services.projects.task_service | INFO | Published task.created event for task abc-123",
         "events:task", "task.created"),

        ("Published task.status_changed event for task test-456",
         "events:task", "task.status_changed"),

        # Session events
        ("Published session.started event for session session-789",
         "events:session", "session.started"),

        ("Published session.ended event for session session-999",
         "events:session", "session.ended"),

        # Whiteboard events
        ("Added task xyz-123 to whiteboard (created as 'doing')",
         "events:system", "whiteboard.task_added"),

        ("Updated task abc-456 on whiteboard: doing → done",
         "events:system", "whiteboard.task_updated"),

        ("Added session session-abc-789 (claude) to whiteboard",
         "events:system", "whiteboard.session_added"),

        ("Removed session session-123 from whiteboard",
         "events:system", "whiteboard.session_removed"),

        # Service events
        ("Event listener service started successfully",
         "events:system", "service.started"),

        ("Auto-Archive service stopped",
         "events:system", "service.stopped"),

        # Backend events
        ("🎉 Archon backend started successfully!",
         "events:system", "backend.started"),

        ("🛑 Shutting down Archon backend...",
         "events:system", "backend.shutdown"),

        # Error/Warning events
        ("ERROR: Database connection failed",
         "events:system", "error.occurred"),

        ("WARNING: Could not start event listener service",
         "events:system", "warning.occurred"),

        # Crawl events
        ("Starting crawl for URL: https://example.com",
         "events:system", "crawl.started"),

        ("Crawl completed for https://example.com",
         "events:system", "crawl.completed"),

        # API requests
        ("GET /api/whiteboard",
         "events:system", "api.request"),

        ("POST /api/projects",
         "events:system", "api.request"),
    ]

    print("=" * 70)
    print("EventDetector Pattern Matching Test")
    print("=" * 70)

    passed = 0
    failed = 0

    for log_line, expected_channel, expected_event_type in test_cases:
        detected = detector.detect_event(log_line, "test-service")

        if detected:
            actual_channel = detected["channel"]
            actual_event_type = detected["event"]["event_type"]

            if actual_channel == expected_channel and actual_event_type == expected_event_type:
                print(f"✅ PASS: {expected_event_type}")
                print(f"   Log: {log_line[:60]}...")
                print(f"   Detected: {actual_channel} / {actual_event_type}")
                if "entity_id" in detected["event"]:
                    print(f"   Entity ID: {detected['event']['entity_id']}")
                passed += 1
            else:
                print(f"❌ FAIL: Expected {expected_channel}/{expected_event_type}")
                print(f"   Got: {actual_channel}/{actual_event_type}")
                failed += 1
        else:
            print(f"❌ FAIL: No event detected for pattern {expected_event_type}")
            print(f"   Log: {log_line}")
            failed += 1

        print()

    # Test noise filtering
    print("=" * 70)
    print("Testing Noise Filtering")
    print("=" * 70)

    # API request should be filtered
    api_detected = detector.detect_event("GET /api/whiteboard", "test")
    should_publish = detector.should_publish_to_events(api_detected) if api_detected else False
    if not should_publish:
        print("✅ API requests correctly filtered (not published to events)")
    else:
        print("❌ API requests should be filtered")
        failed += 1

    # Critical warning should pass
    critical_warn = detector.detect_event("WARNING: Could not start service", "test")
    should_publish = detector.should_publish_to_events(critical_warn) if critical_warn else False
    if should_publish:
        print("✅ Critical warnings correctly published")
    else:
        print("❌ Critical warnings should be published")
        failed += 1

    # Non-critical warning should be filtered
    minor_warn = detector.detect_event("WARNING: Minor issue", "test")
    should_publish = detector.should_publish_to_events(minor_warn) if minor_warn else False
    if not should_publish:
        print("✅ Minor warnings correctly filtered")
        passed += 1
    else:
        print("❌ Minor warnings should be filtered")
        failed += 1

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")

    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n❌ {failed} tests failed")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = test_event_detection()
    sys.exit(exit_code)
