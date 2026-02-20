"""
Alfred Log Collector - Streams logs from Alfred services to Redis
Monitors: alfred-agent, alfred-control-plane, homeassistant, neural-interface
"""
import os
import time
import redis
import docker
from datetime import datetime

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
# Alfred-specific service mapping
MONITORED_CONTAINERS = ["alfred-agent", "alfred-control-plane", "homeassistant", "neural-interface"]

def publish_log(redis_client, service_name, log_line):
    """Publish a formatted log line to Redis with Alfred-specific enrichment and safety audit"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Enrichment: Detect LLM calls or HA interactions
    prefix = ""
    is_high_risk = False
    
    # Safety Audit Logic
    risk_keywords = ["RM -RF", "DELETE", "DROP TABLE", "SHUTDOWN", "TERMINATE", "WIPE"]
    if any(word in log_line.upper() for word in risk_keywords):
        prefix = "🚨 [HIGH RISK] "
        is_high_risk = True
    elif "CALL_SERVICE" in log_line.upper() and ("LIGHT" in log_line.upper() or "SWITCH" in log_line.upper()):
        prefix = "💡 [HA_CMD] "
    elif "CALL_SERVICE" in log_line.upper() and ("CLIMATE" in log_line.upper() or "TEMPERATURE" in log_line.upper()):
        prefix = "🌡️ [HA_CMD] "
    elif "LLM" in log_line.upper() or "GEMINI" in log_line.upper() or "CLAUDE" in log_line.upper():
        prefix = "🧠 "
    elif "HA" in log_line.upper() or "ENTITY" in log_line.upper() or "STATE" in log_line.upper():
        prefix = "🏠 "
    elif "CONTROL" in log_line.upper() or "SANDBOX" in log_line.upper():
        prefix = "🛡️ "
        
    formatted_log = f"[{timestamp}] [{service_name}] {prefix}{log_line}"
    
    if is_high_risk:
        print(f"\n⚠️  SAFETY ALERT: {formatted_log}\n")
        
    try:
        redis_client.publish("logs", formatted_log)
    except Exception as e:
        print(f"❌ Redis publish error: {e}")
    print(formatted_log)  # Also print to stdout

def monitor_container_logs():
    """Monitor logs from Alfred ecosystem containers"""
    redis_client = redis.from_url(REDIS_URL)
    docker_client = docker.from_env()

    print("🕵️ Alfred Log Collector started")
    print(f"📡 Publishing to Redis: {REDIS_URL}")
    print(f"👀 Monitoring Alfred ecosystem: {', '.join(MONITORED_CONTAINERS)}\n")

    # Create log streams for each container
    streams = {}
    for container_name in MONITORED_CONTAINERS:
        try:
            container = docker_client.containers.get(container_name)
            # Fetch last few lines to ensure we see connection success
            streams[container_name] = container.logs(stream=True, follow=True, tail=10)
            publish_log(redis_client, "collector", f"Connected to {container_name}")
        except docker.errors.NotFound:
            publish_log(redis_client, "collector", f"⚠️  Container {container_name} not found")
        except Exception as e:
            publish_log(redis_client, "collector", f"❌ Error connecting to {container_name}: {e}")

    # Monitor all streams
    while True:
        for container_name, stream in streams.items():
            try:
                # next(stream) is blocking. In a real multi-stream monitor,
                # we'd use threads or async, but for a simple script:
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
                # Basic error handling
                time.sleep(0.1)

if __name__ == "__main__":
    try:
        monitor_container_logs()
    except KeyboardInterrupt:
        print("\n👋 Alfred Log Collector stopped")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
