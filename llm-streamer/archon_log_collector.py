"""
Archon Log Collector - Streams logs from Archon services to Redis
Monitors: archon-server, archon-mcp, archon-ui and publishes to Redis pub/sub
"""
import os
import time
import redis
import docker
from datetime import datetime

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
MONITORED_CONTAINERS = ["archon-server", "archon-mcp", "archon-ui"]

def publish_log(redis_client, service_name, log_line):
    """Publish a formatted log line to Redis"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    formatted_log = f"[{timestamp}] [{service_name}] {log_line}"
    redis_client.publish("logs", formatted_log)
    print(formatted_log)  # Also print to stdout

def monitor_container_logs():
    """Monitor logs from multiple Archon containers"""
    redis_client = redis.from_url(REDIS_URL)
    docker_client = docker.from_env()

    print("🔍 Archon Log Collector started")
    print(f"📡 Publishing to Redis: {REDIS_URL}")
    print(f"👀 Monitoring containers: {', '.join(MONITORED_CONTAINERS)}\n")

    # Create log streams for each container
    streams = {}
    for container_name in MONITORED_CONTAINERS:
        try:
            container = docker_client.containers.get(container_name)
            streams[container_name] = container.logs(stream=True, follow=True, tail=0)
            publish_log(redis_client, "collector", f"Connected to {container_name}")
        except docker.errors.NotFound:
            publish_log(redis_client, "collector", f"⚠️  Container {container_name} not found")
        except Exception as e:
            publish_log(redis_client, "collector", f"❌ Error connecting to {container_name}: {e}")

    # Monitor all streams
    while True:
        for container_name, stream in streams.items():
            try:
                log_line = next(stream).decode('utf-8').strip()
                if log_line:
                    publish_log(redis_client, container_name, log_line)
            except StopIteration:
                # Container stopped, try to reconnect
                try:
                    container = docker_client.containers.get(container_name)
                    streams[container_name] = container.logs(stream=True, follow=True, tail=0)
                    publish_log(redis_client, "collector", f"Reconnected to {container_name}")
                except:
                    pass
            except Exception as e:
                publish_log(redis_client, "collector", f"Error reading from {container_name}: {e}")
                time.sleep(1)

if __name__ == "__main__":
    try:
        monitor_container_logs()
    except KeyboardInterrupt:
        print("\n👋 Archon Log Collector stopped")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
