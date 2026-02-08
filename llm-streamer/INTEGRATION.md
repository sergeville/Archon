# LLM_streamer Integration with Archon

## Overview

LLM_streamer has been successfully integrated into the Archon system to provide real-time log streaming from all Archon services.

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Archon       │     │   Redis      │     │   SSE        │
│ Services     │────▶│  Pub/Sub     │────▶│  Dashboard   │
│ (logs)       │     │  (channel)   │     │  (browser)   │
└──────────────┘     └──────────────┘     └──────────────┘
      │
      │ Docker logs
      ▼
┌──────────────┐
│   Log        │
│  Collector   │
└──────────────┘
```

## Services Added

### 1. llm-streamer-redis
- **Image**: redis:alpine
- **Purpose**: Message broker for pub/sub distribution
- **Network**: app-network (shared with Archon)
- **Channel**: "logs"

### 2. llm-streamer-gateway
- **Image**: python:3.11-slim
- **Port**: 8000 (configurable via LLM_STREAMER_PORT)
- **Purpose**: FastAPI server with SSE endpoint and dashboard
- **Endpoints**:
  - `http://localhost:8000` - Minimalist log dashboard
  - `http://localhost:8000/stream` - SSE event stream

### 3. llm-streamer-producer
- **Image**: python:3.11-slim
- **Purpose**: Simulates LLM backend (generates test logs)
- **Publishes to**: Redis "logs" channel

### 4. llm-streamer-collector
- **Image**: python:3.11-slim
- **Purpose**: Monitors Archon services and publishes logs to Redis
- **Monitors**:
  - archon-server (port 8181)
  - archon-mcp (port 8051)
  - archon-ui (port 3737)
- **Access**: Docker socket (read container logs)

## Configuration

### Environment Variables

Added to `.env` and `.env.example`:

```bash
# LLM Streamer Port (Log streaming dashboard)
LLM_STREAMER_PORT=8000
```

### Docker Compose Integration

All services added to `/Users/sergevilleneuve/Documents/Archon/docker-compose.yml`:
- Connected to Archon's `app-network`
- Proper health checks configured
- Dependencies set (collector waits for Archon services)

## Usage

### Start All Services

```bash
cd /Users/sergevilleneuve/Documents/Archon
docker-compose up -d
```

### View Log Streaming Dashboard

```bash
open http://localhost:8000
```

### View Specific Service Logs

```bash
# Gateway (SSE server)
docker logs llm-streamer-gateway

# Collector (Archon log monitor)
docker logs llm-streamer-collector

# Producer (test messages)
docker logs llm-streamer-producer

# Redis
docker logs llm-streamer-redis
```

### Stop LLM Streamer Services

```bash
docker-compose stop llm-streamer-redis llm-streamer-gateway llm-streamer-producer llm-streamer-collector
```

### Remove LLM Streamer Services

To completely remove (edit docker-compose.yml and remove the services, then):

```bash
docker-compose down
docker-compose up -d
```

## Testing

### Test Redis Pub/Sub

```bash
# Publish test message
docker exec llm-streamer-redis redis-cli publish logs "Test message"

# Subscribe to logs channel
docker exec llm-streamer-redis redis-cli subscribe logs
```

### Test SSE Stream

```bash
# Test SSE endpoint
curl -N http://localhost:8000/stream
```

### Test Dashboard

```bash
# Test HTML dashboard
curl http://localhost:8000 | head -15
```

## Features

✅ Real-time log streaming with Server-Sent Events (SSE)
✅ Redis pub/sub for scalable message distribution
✅ Minimalist monospace dashboard with auto-scroll
✅ Docker Compose orchestration
✅ Integrated with Archon's app-network
✅ Health checks on all services
✅ Automatic container log collection from Archon services

## Architecture Benefits

1. **Decoupled**: LLM_streamer services are independent of Archon core functionality
2. **Scalable**: Redis pub/sub allows multiple consumers
3. **Low Latency**: ~1ms pub/sub latency
4. **Integrated**: Shares Archon's Docker network for seamless communication
5. **Observable**: Real-time visibility into all Archon service logs

## Files

```
/Users/sergevilleneuve/Documents/Archon/llm-streamer/
├── main.py                    # FastAPI SSE gateway + dashboard
├── producer.py                # Test log producer
├── archon_log_collector.py    # Archon log collector
├── requirements.txt           # Python dependencies
├── docker-compose.yml         # Standalone compose (reference)
├── README.md                  # LLM_streamer documentation
├── INTEGRATION.md             # This file
└── .git/                      # Git repository
```

## Source Project

The LLM_streamer project was originally created at:
- **Location**: `/Users/sergevilleneuve/Documents/MyExperiments/LLM_streamer/`
- **Status**: Tracked in EXPERIMENTS.md
- **Purpose**: Reusable log streaming pattern for LLM backends

It has been integrated into Archon as a subdirectory while maintaining its independent git repository.

## Next Steps

### Enhancement Ideas

1. **Add time-series visualization** - Chart.js for throughput metrics
2. **Log filtering** - Filter by service, log level, or keywords
3. **Multiple channels** - Separate channels for errors, metrics, debug logs
4. **Token tracking** - Monitor LLM token usage across services
5. **Alerts** - Notification system for critical logs
6. **Persistence** - Optional log storage to database or file

### Production Considerations

- Consider log retention policies
- Add authentication if exposing externally
- Implement log rotation for high-volume systems
- Monitor Redis memory usage

## Troubleshooting

### Dashboard shows no logs

1. Check if Redis is running:
   ```bash
   docker ps | grep llm-streamer-redis
   ```

2. Check if collector is running:
   ```bash
   docker ps | grep llm-streamer-collector
   ```

3. Manually publish test message:
   ```bash
   docker exec llm-streamer-redis redis-cli publish logs "Test"
   ```

### Services won't start

1. Check for port conflicts:
   ```bash
   lsof -i :8000
   ```

2. Check Docker logs:
   ```bash
   docker-compose logs llm-streamer-gateway
   ```

3. Verify environment variables:
   ```bash
   grep LLM_STREAMER /Users/sergevilleneuve/Documents/Archon/.env
   ```

## Status

**✅ Integration Complete** - All services running and operational.

**Date Integrated**: 2026-02-07
**Archon Version**: Current
**LLM_streamer Version**: 1.0
