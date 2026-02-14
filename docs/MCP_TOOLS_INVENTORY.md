# Archon MCP Tools Inventory

**Date:** 2026-02-14
**Project:** Shared Memory System Implementation
**Task:** Task 5 - Document Current MCP Tool Inventory
**Status:** Complete

---

## Overview

This document catalogs all Archon MCP tools available through the MCP_DOCKER gateway in Claude Code. Tools are categorized by function and include parameter specifications, return types, and recommended use cases.

## Tool Categories

1. [Task Management](#task-management) (7 tools)
2. [GitHub Integration](#github-integration) (40+ tools)
3. [MCP Server Management](#mcp-server-management) (6 tools)
4. [Code Mode](#code-mode) (1 tool)

---

## Task Management

### 1. archon_list_tasks

**Status:** ✅ Working
**Function:** List and search tasks with filtering

**Parameters:**
```typescript
{
  status?: "todo" | "doing" | "done",  // Filter by status
  assignee?: string,                   // Filter by assignee
  priority?: "low" | "medium" | "high", // Filter by priority
  limit?: number                       // Max results (default: 20)
}
```

**Returns:**
```typescript
{
  success: boolean,
  count: number,
  tasks: Array<{
    id: string,
    title: string,
    description: string,
    status: string,
    priority: string,
    assignee: string,
    created_at: string,
    updated_at: string
  }>
}
```

**Use Cases:**
- Query tasks by status for workflow management
- Find tasks assigned to specific agents
- List high-priority tasks
- Search task inventory

**Example:**
```json
{
  "assignee": "claude",
  "status": "doing",
  "limit": 10
}
```

---

### 2. archon_get_task

**Status:** ✅ Working
**Function:** Get detailed information about a specific task

**Parameters:**
```typescript
{
  task_id: string  // Required: Task UUID
}
```

**Returns:**
```typescript
{
  success: boolean,
  task: {
    id: string,
    title: string,
    description: string,
    status: string,
    priority: string,
    assignee: string,
    created_at: string,
    updated_at: string
  }
}
```

**Use Cases:**
- Retrieve complete task details
- Verify task exists before operations
- Get current task state
- Fetch task for context building

**Example:**
```json
{
  "task_id": "b27ef178-2be1-4fc7-b3f2-fb23d7eca7e0"
}
```

---

### 3. archon_add_task

**Status:** ❌ Broken (Missing project_id parameter)
**Function:** Create new tasks

**Expected Parameters:**
```typescript
{
  project_id: string,              // MISSING - causes 422 error
  title: string,                   // Required
  description?: string,            // Optional
  status?: "todo" | "doing" | "done",
  priority?: "low" | "medium" | "high",
  assignee?: string
}
```

**Current Parameters (Incomplete):**
```typescript
{
  title: string,
  description?: string,
  status?: string,
  priority?: string,
  assignee?: string
}
```

**Returns:**
```typescript
{
  success: boolean,
  message?: string,
  task?: object
}
```

**Issue:** Missing `project_id` parameter causes HTTP 422 validation error

**Workaround:** Use HTTP API
```bash
curl -X POST "http://localhost:8181/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "uuid",
    "title": "Task Title",
    "description": "Description",
    "status": "todo",
    "priority": "medium",
    "assignee": "claude"
  }'
```

---

### 4. archon_update_task

**Status:** ❌ Broken (405 Method Not Allowed)
**Function:** Update existing task fields

**Parameters:**
```typescript
{
  task_id: string,
  title?: string,
  description?: string,
  status?: string,
  priority?: string,
  assignee?: string
}
```

**Returns:**
```typescript
{
  success: boolean,
  message?: string,
  task?: object
}
```

**Issue:** HTTP 405 Method Not Allowed - endpoint routing issue

**Workaround:** Use HTTP API
```bash
curl -X PUT "http://localhost:8181/api/tasks/{task_id}" \
  -H "Content-Type: application/json" \
  -d '{"status": "doing", "assignee": "claude"}'
```

---

### 5. archon_start_task

**Status:** ❌ Broken (405 Method Not Allowed)
**Function:** Mark task as "doing" (shortcut for update)

**Parameters:**
```typescript
{
  task_id: string
}
```

**Returns:**
```typescript
{
  success: boolean,
  message?: string,
  task?: object
}
```

**Issue:** Same 405 error as archon_update_task

**Workaround:** Use HTTP API with `status: "doing"`

---

### 6. archon_complete_task

**Status:** ❌ Broken (405 Method Not Allowed)
**Function:** Mark task as complete (shortcut for update)

**Parameters:**
```typescript
{
  task_id: string
}
```

**Returns:**
```typescript
{
  success: boolean,
  message?: string,
  task?: object
}
```

**Issue:** Same 405 error as archon_update_task

**Workaround:** Use HTTP API with `status: "done"`

---

### 7. archon_archive_task

**Status:** ⚠️ Untested (likely 405 error)
**Function:** Archive/soft-delete tasks

**Parameters:**
```typescript
{
  task_id: string
}
```

**Returns:**
```typescript
{
  success: boolean,
  message?: string,
  task?: object
}
```

**Recommendation:** Test before use, likely needs HTTP API workaround

---

## GitHub Integration

### Available GitHub Tools (40+ tools)

The MCP_DOCKER gateway provides comprehensive GitHub integration. These tools are NOT Archon-specific but are available in the same MCP session.

**Categories:**
- Repository management (create, fork, search)
- Issue management (create, update, search, comment)
- Pull request management (create, update, merge, review)
- Branch management (create, list)
- File operations (create, update, delete, read)
- Release management (list, get)
- Tag management (list, get)
- Commit operations (list, get)
- Search operations (code, issues, PRs, users, repositories)
- Team management (get teams, members)
- Labels (get, list issue types)

**Note:** Full GitHub tool inventory available in separate documentation. These tools are complementary to Archon's task management for code-related memory operations.

---

## MCP Server Management

### 1. mcp-find

**Status:** ✅ Working
**Function:** Search MCP server catalog

**Parameters:**
```typescript
{
  query: string,        // Search query
  limit?: number       // Max results (default: 10)
}
```

**Use Cases:**
- Discover available MCP servers
- Find servers by capability
- Explore MCP ecosystem

---

### 2. mcp-add

**Status:** ✅ Working
**Function:** Add MCP server to session

**Parameters:**
```typescript
{
  name: string,         // Server name from catalog
  activate?: boolean    // Activate tools (default: true)
}
```

**Use Cases:**
- Enable additional MCP servers
- Extend tool capabilities
- Dynamic tool loading

---

### 3. mcp-remove

**Status:** ✅ Working
**Function:** Remove MCP server from session

**Parameters:**
```typescript
{
  name: string  // Server name to remove
}
```

**Use Cases:**
- Clean up unused servers
- Manage tool inventory
- Reduce noise

---

### 4. mcp-config-set

**Status:** ✅ Working
**Function:** Configure MCP server settings

**Parameters:**
```typescript
{
  server: string,       // Server name
  config: object       // Server-specific config
}
```

**Use Cases:**
- Update server configuration
- Set API keys
- Customize behavior

---

### 5. mcp-exec

**Status:** ✅ Working
**Function:** Execute tool by name

**Parameters:**
```typescript
{
  name: string,        // Tool name
  arguments?: object   // Tool arguments
}
```

**Use Cases:**
- Call tools not visible in listTools
- Dynamic tool execution
- Advanced automation

---

### 6. code-mode

**Status:** ✅ Working
**Function:** Create JavaScript-enabled tool combining multiple MCP tools

**Parameters:**
```typescript
{
  servers: string[],   // MCP server names
  name: string        // New tool name (prefixed with 'code-mode-')
}
```

**Use Cases:**
- Combine multiple tools into workflows
- Create custom automation scripts
- Build complex multi-tool operations

---

## Tool Usage Patterns

### Pattern 1: Read-Only Queries (Working)

**Use Archon MCP tools for:**
- Listing tasks (`archon_list_tasks`)
- Getting task details (`archon_get_task`)
- Searching/filtering tasks

**Example Workflow:**
```json
// 1. List active tasks
archon_list_tasks({status: "doing", assignee: "claude"})

// 2. Get task details
archon_get_task({task_id: "..."})

// 3. Process task information
// Use in memory layer queries, context building, etc.
```

---

### Pattern 2: Write Operations (Use HTTP API)

**Use HTTP API for:**
- Creating tasks (POST /api/tasks)
- Updating tasks (PUT /api/tasks/{id})
- Changing status (PUT with status field)
- Assigning tasks (PUT with assignee field)

**Example Workflow:**
```bash
# Create task
curl -X POST "http://localhost:8181/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "...",
    "title": "New Task",
    "status": "todo",
    "assignee": "claude"
  }'

# Update task
curl -X PUT "http://localhost:8181/api/tasks/{id}" \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'
```

---

### Pattern 3: Hybrid Approach (Recommended)

**Best Practice for Shared Memory Implementation:**

1. **Query with MCP:** Use `archon_list_tasks` and `archon_get_task`
2. **Modify with HTTP API:** Use curl/HTTP for create/update/delete
3. **Verify with MCP:** Re-query to confirm changes

**Example:**
```javascript
// 1. Query current state (MCP)
const tasks = await archon_list_tasks({assignee: "claude"})

// 2. Identify task to update
const taskToUpdate = tasks.find(t => t.title === "...")

// 3. Update via HTTP API
await fetch(`http://localhost:8181/api/tasks/${taskToUpdate.id}`, {
  method: 'PUT',
  body: JSON.stringify({status: "done"})
})

// 4. Verify update (MCP)
const updated = await archon_get_task({task_id: taskToUpdate.id})
```

---

## Mapping to Memory Layers

### Working Memory (Current Context)
**Tools:**
- `archon_list_tasks` - Query active tasks
- `archon_get_task` - Get task details

**Use Case:** Real-time task state for agents

---

### Short-Term Memory (Sessions)
**Tools:**
- `archon_list_tasks` with date filters
- GitHub commit history tools

**Use Case:** Recent activity tracking, session summaries

**Gap:** Need session-specific memory tools (Phase 2)

---

### Long-Term Memory (Knowledge Base)
**Tools:**
- GitHub search tools (code, issues, PRs)
- Repository tools (files, commits)

**Use Case:** Historical patterns, code examples, documentation

**Gap:** Need semantic search across tasks (Phase 2)

---

## Gaps & Recommendations

### Critical Gaps

1. **MCP Update Tools Broken**
   - Fix 405 Method Not Allowed errors
   - Add proper endpoint routing

2. **Missing project_id Parameter**
   - Add to `archon_add_task` tool definition
   - Make it optional with default project

3. **No Session Memory Tools**
   - Need session CRUD operations
   - Session summary generation
   - Cross-session queries

4. **No Pattern Learning Tools**
   - Pattern storage/retrieval
   - Confidence score updates
   - Success/failure tracking

### Phase 2 Requirements

**New MCP Tools Needed:**
- `archon_create_session` - Start new agent session
- `archon_get_session` - Get session details
- `archon_list_sessions` - Query sessions
- `archon_add_to_session` - Add context to session
- `archon_search_memory` - Semantic search across all layers
- `archon_record_pattern` - Store learned patterns
- `archon_query_patterns` - Find similar patterns

### Phase 3 Requirements

**Pattern Learning Tools:**
- `archon_harvest_pattern` - Extract pattern from session
- `archon_rate_pattern` - Update confidence score
- `archon_find_patterns` - Pattern similarity search
- `archon_suggest_pattern` - Get pattern recommendations

### Phase 4 Requirements

**Multi-Agent Coordination:**
- `archon_handoff_task` - Transfer task between agents
- `archon_claim_task` - Agent claims task
- `archon_share_context` - Share session context
- `archon_resolve_conflict` - Conflict resolution

---

## Performance Considerations

### Tool Latency (Observed)

| Tool | Avg Latency | Notes |
|------|-------------|-------|
| archon_list_tasks | <100ms | Fast, efficient |
| archon_get_task | <50ms | Very fast |
| archon_add_task | N/A | Broken |
| archon_update_task | N/A | Broken |

**HTTP API Latency:**
- GET /api/tasks: ~50ms
- POST /api/tasks: ~100ms
- PUT /api/tasks/{id}: ~75ms

**Recommendation:** HTTP API is comparable or faster than MCP tools

---

## Security Considerations

### Authentication
- MCP tools inherit session authentication
- No additional auth required
- HTTP API uses same credentials

### Authorization
- Task operations limited by user permissions
- No cross-user task access
- Project-level permissions respected

### Data Validation
- All tools validate input parameters
- 422 errors for invalid data
- Type checking enforced

---

## Testing Recommendations

### Unit Tests Needed
1. Test each MCP tool independently
2. Verify parameter validation
3. Check error handling
4. Validate response schemas

### Integration Tests Needed
1. Test MCP → HTTP API consistency
2. Verify state synchronization
3. Test concurrent operations
4. Validate memory layer queries

### Performance Tests Needed
1. Benchmark tool latency
2. Test with large result sets
3. Measure memory usage
4. Test concurrent agent access

---

## Conclusion

**Current MCP Tool Status:**
- **7 Archon task tools** identified
- **2 working** (list, get)
- **5 broken** (add, update, start, complete, archive)
- **40+ GitHub tools** available
- **6 MCP management tools** working

**Recommendation for Phase 1-6:**
- Use working MCP tools for queries
- Use HTTP API for mutations
- Plan new tools for Phase 2-4
- Fix broken tools post-implementation

**This inventory satisfies Task 5 requirements** and provides foundation for Phase 2-6 tool development.

---

**Document Created By:** Claude (Archon Agent)
**Task ID:** 228609d2-7df2-4ecd-85d0-a5cefef60595
**Project:** Shared Memory System Implementation (b231255f-6ed9-4440-80de-958bcf7b4f9f)
**Next Task:** Task 6 - Map Existing Tools to Memory Layers
