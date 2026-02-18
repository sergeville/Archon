"""
Archon Log Collector - Enhanced with Event Detection

Streams logs from Archon services to Redis and detects structured events.
Monitors: archon-server, archon-mcp, archon-ui
Publishes:
- Raw logs to "logs" channel (for UI display)
- Structured events to "events:task", "events:session", "events:system" (for whiteboard)
"""
import os
import time
import json
import redis
import docker
from datetime import datetime
from event_detector import EventDetector

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
MONITORED_CONTAINERS = ["archon-server", "archon-mcp", "archon-ui"]

class EnhancedLogCollector:
    """Enhanced log collector with event detection"""

    def __init__(self):
        """Initialize collector with Redis and Docker clients"""
        self.redis_client = redis.from_url(REDIS_URL)
        self.docker_client = docker.from_env()
        self.event_detector = EventDetector()
        self.stats = {
            "logs_published": 0,
            "events_detected": 0,
            "events_by_type": {}
        }

    def publish_log(self, service_name: str, log_line: str):
        """
        Publish a formatted log line to Redis logs channel.

        Args:
            service_name: Name of the service (archon-server, archon-mcp, etc.)
            log_line: Raw log line from Docker
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_log = f"[{timestamp}] [{service_name}] {log_line}"
        self.redis_client.publish("logs", formatted_log)
        self.stats["logs_published"] += 1
        print(formatted_log)  # Also print to stdout

    def publish_event(self, channel: str, event: dict):
        """
        Publish a structured event to Redis events channel.

        Args:
            channel: Redis channel (events:task, events:session, events:system)
            event: Structured event dict
        """
        try:
            event_json = json.dumps(event)
            self.redis_client.publish(channel, event_json)
            self.stats["events_detected"] += 1

            # Track event types
            event_type = event.get("event_type", "unknown")
            self.stats["events_by_type"][event_type] = \
                self.stats["events_by_type"].get(event_type, 0) + 1

            # Log event detection
            entity_id = event.get("entity_id", "N/A")
            print(f"📊 Event detected: {event_type} (entity: {entity_id}) → {channel}")

        except Exception as e:
            print(f"❌ Error publishing event: {e}")

    def process_log_line(self, service_name: str, log_line: str):
        """
        Process a log line: publish raw log + detect and publish events.

        Args:
            service_name: Name of the service
            log_line: Raw log line
        """
        # Always publish raw log for UI display
        self.publish_log(service_name, log_line)

        # Try to detect structured events
        detected = self.event_detector.detect_event(log_line, service_name)
        if detected:
            # Check if we should publish this event
            if self.event_detector.should_publish_to_events(detected):
                self.publish_event(detected["channel"], detected["event"])

    def print_stats(self):
        """Print collection statistics"""
        print("\n" + "=" * 60)
        print("📈 Archon Log Collector Statistics")
        print("=" * 60)
        print(f"Logs published: {self.stats['logs_published']}")
        print(f"Events detected: {self.stats['events_detected']}")
        if self.stats["events_by_type"]:
            print("\nEvents by type:")
            for event_type, count in sorted(
                self.stats["events_by_type"].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                print(f"  {event_type}: {count}")
        print("=" * 60 + "\n")

    def monitor_container_logs(self):
        """Monitor logs from multiple Archon containers"""
        print("🔍 Archon Log Collector (Enhanced) started")
        print(f"📡 Publishing to Redis: {REDIS_URL}")
        print(f"👀 Monitoring containers: {', '.join(MONITORED_CONTAINERS)}")
        print("📊 Event detection enabled\n")

        # Create log streams for each container
        streams = {}
        for container_name in MONITORED_CONTAINERS:
            try:
                container = self.docker_client.containers.get(container_name)
                streams[container_name] = container.logs(stream=True, follow=True, tail=0)
                self.publish_log("collector", f"Connected to {container_name}")
            except docker.errors.NotFound:
                self.publish_log("collector", f"⚠️  Container {container_name} not found")
            except Exception as e:
                self.publish_log("collector", f"❌ Error connecting to {container_name}: {e}")

        # Monitor all streams
        last_stats_time = time.time()
        try:
            while True:
                for container_name, stream in streams.items():
                    try:
                        log_line = next(stream).decode('utf-8').strip()
                        if log_line:
                            self.process_log_line(container_name, log_line)
                    except StopIteration:
                        # Container stopped, try to reconnect
                        try:
                            container = self.docker_client.containers.get(container_name)
                            streams[container_name] = container.logs(stream=True, follow=True, tail=0)
                            self.publish_log("collector", f"Reconnected to {container_name}")
                        except:
                            pass
                    except Exception as e:
                        self.publish_log("collector", f"Error reading from {container_name}: {e}")
                        time.sleep(1)

                # Print stats every 5 minutes
                if time.time() - last_stats_time > 300:
                    self.print_stats()
                    last_stats_time = time.time()

        except KeyboardInterrupt:
            self.print_stats()
            raise

def main():
    """Main entry point"""
    collector = EnhancedLogCollector()
    try:
        collector.monitor_container_logs()
    except KeyboardInterrupt:
        print("\n👋 Archon Log Collector stopped")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()
