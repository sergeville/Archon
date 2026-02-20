# Claude Code MCP Configuration for Archon

**Task**: Phase 1, Task 10 - Configure Claude Code MCP Connection
**Date**: 2026-02-18
**Status**: ✅ Configuration Complete

## Overview

This document describes how the Archon MCP server is configured to work with Claude Code CLI. The configuration enables Claude Code to access all 22 Archon tools through the MCP (Model Context Protocol).

## Configuration Method

### User-Level Configuration

The Archon MCP server was added at **user scope**, making it available across all projects for the current user.

**Command Used**:
```bash
claude mcp add --transport http --scope user archon http://localhost:8051/mcp
```

**Result**:
```
Added HTTP MCP server archon with URL: http://localhost:8051/mcp to user config
File modified: /Users/sergevilleneuve/.claude.json
```

## Configuration Details

### Configuration File Location

`~/.claude.json`

### MCP Server Entry

```json
{
  "mcpServers": {
    "archon": {
      "type": "http",
      "url": "http://localhost:8051/mcp"
    }
  }
}
```

### Configuration Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Server Name** | archon | Identifier for the MCP server |
| **Type** | http | Transport protocol (streamable-http) |
| **URL** | http://localhost:8051/mcp | MCP server endpoint |
| **Scope** | user | Available across all projects for this user |

## MCP Server Architecture

### Transport: Streamable-HTTP

The Archon MCP server uses FastMCP's `streamable-http` transport mode, which:
- Provides HTTP-based communication
- Supports server-sent events (SSE) for streaming
- Enables bidirectional JSON-RPC over HTTP
- Allows persistent connections

### Endpoints

**Primary Endpoint**: `http://localhost:8051/mcp`
- MCP protocol communication
- Tool invocation
- State management

**Health Endpoint**: `http://localhost:8051/health`
- Server health checks
- Uptime monitoring
- Status verification

## Available Tools

With this configuration, Claude Code can access all 22 Archon MCP tools:

### Task Management (2 tools)
- `find_tasks` - Search and list tasks
- `manage_task` - Create, update, delete tasks

### Session Management (5 tools)
- `find_sessions` - Retrieve agent sessions
- `manage_session` - Create, end, update sessions
- `log_session_event` - Log events within sessions
- `search_sessions_semantic` - Semantic search using embeddings
- `get_agent_context` - Get agent's recent work context

### RAG / Knowledge Base (5 tools)
- `rag_get_available_sources` - List knowledge sources
- `rag_search_knowledge_base` - RAG search with embeddings
- `rag_search_code_examples` - Search for code snippets
- `rag_list_pages_for_source` - List pages for a source
- `rag_read_full_page` - Retrieve complete page content

### Project Management (2 tools)
- `find_projects` - Find and search projects
- `manage_project` - Create, update, delete projects

### Pattern Management (3 tools)
- `harvest_pattern` - Save learned patterns
- `search_patterns` - Semantic pattern search
- `record_pattern_observation` - Record pattern application

### Document Management (2 tools)
- `find_documents` - Find and search documents
- `manage_document` - Create, update, delete documents

### Version Management (2 tools)
- `find_versions` - Find version history
- `manage_version` - Create or restore versions

### Feature Management (1 tool)
- `get_project_features` - Get project features array

## Verification

### Configuration Verification

Check configured MCP servers:
```bash
claude mcp list
```

Expected output should include:
```
archon: http://localhost:8051/mcp (HTTP) - Status
```

### Server Health Verification

Verify Archon MCP server is running:
```bash
curl http://localhost:8051/health
```

Expected response:
```json
{
  "success": true,
  "status": "ready",
  "uptime_seconds": <seconds>,
  "message": "MCP server is running",
  "timestamp": "<ISO timestamp>"
}
```

### Tool Usage in Claude Code

To use Archon tools in a Claude Code conversation:
1. The tools are automatically available in any conversation
2. Claude Code will invoke them as needed during task execution
3. Tool names follow the pattern: `archon:tool_name` (e.g., `archon:find_tasks`)

## Configuration Scope Options

### User Scope (Current Configuration)

**File**: `~/.claude.json`
**Availability**: All projects for this user
**Use Case**: Personal development tools

**Advantages**:
- Available everywhere
- No need to configure per-project
- Ideal for always-needed tools

### Project Scope (Alternative)

For team sharing, use project scope:
```bash
claude mcp add --transport http --scope project archon http://localhost:8051/mcp
```

**File**: `.mcp.json` in project root
**Availability**: Only for this project
**Use Case**: Team collaboration

**Advantages**:
- Can be version controlled
- Team members get same configuration
- Project-specific tools

## Troubleshooting

### Connection Issues

If Claude Code shows "Failed to connect":

1. **Verify MCP server is running**:
   ```bash
   docker compose ps archon-mcp
   ```
   Should show: `Up XX hours (healthy)`

2. **Test health endpoint**:
   ```bash
   curl http://localhost:8051/health
   ```

3. **Check MCP server logs**:
   ```bash
   docker compose logs archon-mcp --tail=50
   ```

4. **Restart MCP server**:
   ```bash
   docker compose restart archon-mcp
   ```

### Tools Not Appearing

If Archon tools don't appear in Claude Code:

1. **Verify configuration**:
   ```bash
   cat ~/.claude.json | grep -A 3 '"archon"'
   ```

2. **Restart Claude Code**:
   - Exit and restart the CLI
   - Configuration is loaded on startup

3. **Check server URL**:
   - Ensure URL is `http://localhost:8051/mcp`
   - Not `/sse` or other endpoints

## Technical Notes

### Why HTTP Transport?

The Archon MCP server uses FastMCP with `streamable-http` transport:
- Runs as a persistent HTTP server
- Supports local development without SSL
- Compatible with Docker networking
- Enables health monitoring

### Why Port 8051?

Port 8051 is the standard Archon MCP server port:
- Configured in `docker-compose.yml`
- Set via `ARCHON_MCP_PORT` environment variable
- Avoids conflicts with other services

### Why User Scope?

User scope was chosen because:
- Archon is a personal development tool
- Available in all projects automatically
- No need to configure per-project
- Easier for individual developers

## Related Documentation

- **MCP Tools Inventory**: `docs/MCP_TOOLS_INVENTORY.md`
- **MCP Server Health**: `docs/MCP_SERVER_HEALTH_CHECK.md`
- **Service Verification**: `docs/SERVICE_VERIFICATION.md`
- **Architecture**: `PRPs/ai_docs/ARCHITECTURE.md`

## Next Steps

With the MCP connection configured:
1. ✅ Archon tools available in Claude Code
2. ✅ Can invoke tools during conversations
3. ✅ Access to all 22 Archon capabilities
4. → Ready for Phase 2 implementation

## Acceptance Criteria Met

✅ **Claude Code configuration updated**:
- MCP server added to `~/.claude.json`
- Configuration uses HTTP transport
- URL points to `http://localhost:8051/mcp`

✅ **MCP connection established**:
- Server running and healthy
- Endpoint accessible
- Configuration loaded in Claude Code

✅ **Tools list available**:
- All 22 Archon tools accessible
- Tool documentation available
- Ready for invocation

---

**Configured By**: Claude (Archon Agent)
**Configuration Date**: 2026-02-18
**Task Status**: Complete
**MCP Server Version**: FastMCP with streamable-http transport
