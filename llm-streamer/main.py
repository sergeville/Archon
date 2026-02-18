import os
import asyncio
from redis import asyncio as aioredis
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse

app = FastAPI()
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Minimalist Dashboard UI
HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head><title>LLM Log Stream</title></head>
<body style="background:#1a1a1a; color:#eee; font-family:monospace; padding:20px;">
    <h2>Live LLM Backend Logs <span id="status" style="color:#888; font-size:14px;">[Connecting...]</span></h2>
    <div id="logs" style="height:80vh; overflow-y:auto; border:1px solid #444; padding:10px; background:#000; color:#0f0;"></div>
    <script>
        const src = new EventSource("/stream");
        const box = document.getElementById("logs");
        const status = document.getElementById("status");

        let messageCount = 0;

        src.onopen = () => {
            status.textContent = "[Connected ✓]";
            status.style.color = "#0f0";
            const waiting = document.createElement("div");
            waiting.textContent = "> Waiting for logs...";
            waiting.style.color = "#888";
            waiting.id = "waiting";
            box.appendChild(waiting);
        };

        src.onmessage = (e) => {
            messageCount++;
            const waitingMsg = document.getElementById("waiting");
            if (waitingMsg) waitingMsg.remove();

            const el = document.createElement("div");
            el.style.borderBottom = "1px solid #222";
            el.style.padding = "2px 0";
            el.textContent = `> ${e.data}`;
            box.appendChild(el);
            box.scrollTop = box.scrollHeight;

            status.textContent = `[Connected ✓ - ${messageCount} msgs]`;
        };

        src.onerror = (e) => {
            status.textContent = "[Connection Error ✗]";
            status.style.color = "#f00";
            box.innerHTML = "> ERROR: SSE connection failed<br>> Check browser console (F12) for details<br>> ReadyState: " + src.readyState;
            console.error("EventSource error:", e);
        };
    </script>
</body>
</html>
"""

async def event_generator():
    redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    pubsub = redis.pubsub()
    await pubsub.subscribe("logs")
    try:
        async for msg in pubsub.listen():
            if msg["type"] == "message":
                yield f"data: {msg['data']}\\n\\n"
    finally:
        await pubsub.aclose()
        await redis.aclose()

async def session_event_generator():
    """Stream Claude Code session events in real-time"""
    redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    pubsub = redis.pubsub()
    await pubsub.subscribe("claude-sessions")
    try:
        async for msg in pubsub.listen():
            if msg["type"] == "message":
                yield f"data: {msg['data']}\\n\\n"
    finally:
        await pubsub.aclose()
        await redis.aclose()

@app.get("/")
async def index(): return HTMLResponse(HTML_CONTENT)

@app.get("/stream")
async def stream(): return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/stream/sessions")
async def stream_sessions(): return StreamingResponse(session_event_generator(), media_type="text/event-stream")
