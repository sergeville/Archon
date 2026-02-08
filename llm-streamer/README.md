# LLM_streamer - LLM Log Streaming System

**Real-time log streaming dashboard for LLM backends using Redis Pub/Sub and Server-Sent Events (SSE).**

## Overview

LLM_streamer is a lightweight, production-ready system for streaming logs from LLM backends to a web dashboard in real-time. It uses Redis pub/sub for message distribution and Server-Sent Events (SSE) for efficient browser streaming.

## Architecture

```
┌─────────────┐      ┌─────────┐      ┌──────────────┐
│   LLM       │      │         │      │   Web        │
│   Backend   │─────▶│  Redis  │─────▶│   Dashboard  │
│  (Producer) │      │ Pub/Sub │      │  (SSE Stream)│
└─────────────┘      └─────────┘      └──────────────┘
```

### Components

1. **Redis** - Message broker for pub/sub distribution
2. **Gateway (main.py)** - FastAPI server providing SSE endpoint and dashboard
3. **Producer (producer.py)** - Simulates LLM backend publishing logs
4. **Dashboard** - Minimalist HTML/JS interface with auto-scroll

## Features

- ✅ Real-time log streaming with SSE
- ✅ Redis pub/sub for scalable message distribution
- ✅ Minimalist monospace dashboard
- ✅ Auto-scrolling log view
- ✅ Docker Compose orchestration
- ✅ Scalable producer architecture (run multiple instances)

## Quick Start

### 1. Start the System

```bash
docker-compose up -d
```

### 2. View Dashboard

Open browser to: `http://localhost:8000`

### 3. Scale Producers (Optional)

Increase log volume by running multiple producers:

```bash
docker-compose up -d --scale producer=3
```

### 4. Stop the System

```bash
docker-compose down
```

## Project Structure

```
archon/
├── main.py              # SSE Gateway + Dashboard
├── producer.py          # Backend log simulator
├── requirements.txt     # Python dependencies
├── docker-compose.yml   # Docker orchestration
└── README.md           # This file
```

## Dependencies

- FastAPI - Web framework
- Uvicorn - ASGI server
- Redis - Message broker
- aioredis - Async Redis client

## Configuration

Set Redis URL via environment variable:

```bash
export REDIS_URL="redis://localhost:6379"
```

Or modify in `docker-compose.yml`.

## Use Cases

- **LLM Backend Monitoring** - Stream generation logs, token counts, context updates
- **Multi-Agent Systems** - Monitor multiple AI agents in real-time
- **Development & Debugging** - Live view of backend operations
- **Production Observability** - Track LLM performance metrics

## Extending LLM_streamer

### Add Custom Log Messages

Edit `producer.py` to publish domain-specific logs:

```python
messages = [
    "Token generation: 1024 tokens/sec",
    "Context window: 8192 tokens used",
    "Model: gpt-4 | Latency: 234ms"
]
```

### Multiple Channels

Subscribe to different Redis channels for organized log streams:

```python
await pubsub.subscribe("logs:errors", "logs:metrics", "logs:debug")
```

### Time-Series Visualization

Future enhancement: Add Chart.js for real-time throughput graphs.

## Technical Details

### SSE vs WebSockets

LLM_streamer uses SSE (Server-Sent Events) instead of WebSockets because:
- Simpler implementation (unidirectional)
- Auto-reconnection built-in
- Native browser support
- Perfect for log streaming (server → client)

### Redis Pub/Sub Benefits

- Decouples producers from consumers
- Scales horizontally (multiple producers/subscribers)
- Low latency (~1ms)
- Fire-and-forget semantics

## Status

**🔄 In Progress** - Core system complete, enhancements planned.

## License

MIT

## Author

Created for the MyExperiments workspace as a reusable pattern for LLM observability.
