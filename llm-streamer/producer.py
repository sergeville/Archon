import os
import redis
import time
import random

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
client = redis.from_url(REDIS_URL)

messages = ["Generating tokens...", "Context window optimized", "KV Cache updated", "Streaming response..."]

while True:
    log_line = f"[{time.strftime('%H:%M:%S')}] {random.choice(messages)}"
    client.publish("logs", log_line)
    time.sleep(random.uniform(0.5, 1.5))
