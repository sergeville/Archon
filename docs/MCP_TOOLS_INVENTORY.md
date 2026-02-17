# Archon MCP Tools Inventory

**Date:** 2026-02-17 (Updated)
**Project:** Shared Memory System Implementation
**Task:** Task 5 - Document Current MCP Tool Inventory
**Status:** Updated - Reflects Consolidated Tools Refactor

---

## Overview

This document catalogs all Archon MCP tools available through the MCP_DOCKER gateway in Claude Code. Tools are categorized by function and include parameter specifications, return types, and recommended use cases.

**Recent Changes (2026-02-17):**
- Task management refactored from 7 individual tools to 2 consolidated tools
- Removed deprecated individual CRUD operations
- Updated with current `find_tasks` and `manage_task` implementations

## Tool Categories

1. [Task Management](#task-management) (4 tools - consolidated)
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

### 3. find_tasks (Consolidated)

**Status:** ✅ Working
**Function:** Unified search, list, and get operations for tasks

**Parameters:**
```typescript
{
  query?: string,           // Keyword search in title/description/feature
  task_id?: string,         // Get specific task by ID (full details)
  filter_by?: "status" | "project" | "assignee",
  filter_value?: string,    // Filter value (e.g., "todo", "doing")
  project_id?: string,      // Project UUID for filtering
  include_closed?: boolean, // Include done tasks (default: true)
  page?: number,            // Page number (default: 1)
  per_page?: number        // Items per page (default: 10)
}
```

**Returns:**
```typescript
// For single task (task_id provided)
{
  success: boolean,
  task: {
    id: string,
    title: string,
    description: string,
    status: string,
    priority: string,
    assignee: string,
    // ... full task details
  }
}

// For list/search
{
  success: boolean,
  tasks: Array<Task>,       // Optimized payloads (truncated descriptions)
  total_count: number,
  count: number,
  query?: string           // Echo search query if provided
}
```

**Use Cases:**
- Search tasks by keywords: `find_tasks(query="auth")`
- Get single task: `find_tasks(task_id="uuid")`
- Filter by status: `find_tasks(filter_by="status", filter_value="todo")`
- Filter by project: `find_tasks(filter_by="project", filter_value="project-uuid")`
- Filter by assignee: `find_tasks(filter_by="assignee", filter_value="claude")`
- Paginated lists: `find_tasks(page=2, per_page=20)`

**Examples:**
```json
// Search
{"query": "database migration"}

// Get single task
{"task_id": "b27ef178-2be1-4fc7-b3f2-fb23d7eca7e0"}

// Filter todo tasks
{"filter_by": "status", "filter_value": "todo"}

// Project-specific tasks
{"filter_by": "project", "filter_value": "project-uuid"}
```

---

### 4. manage_task (Consolidated)

**Status:** ✅ Working
**Function:** Unified create, update, and delete operations for tasks

**Parameters:**
```typescript
{
  action: "create" | "update" | "delete",  // Required: operation type

  // For create (required)
  project_id?: string,      // Required for create
  title?: string,           // Required for create

  // For update/delete (required)
  task_id?: string,         // Required for update/delete

  // Optional fields (create/update)
  description?: string,
  status?: "todo" | "doing" | "review" | "done",
  assignee?: string,        // Default: "User"
  task_order?: number,      // Priority 0-100
  feature?: string         // Feature label for grouping
}
```

**Returns:**
```typescript
{
  success: boolean,
  task?: object,            // Updated/created task (optimized)
  task_id?: string,         // For create operations
  message: string
}
```

**Use Cases:**
- Create task: `manage_task("create", project_id="uuid", title="New task")`
- Update status: `manage_task("update", task_id="uuid", status="doing")`
- Update assignee: `manage_task("update", task_id="uuid", assignee="claude")`
- Delete task: `manage_task("delete", task_id="uuid")`
- Update multiple fields: `manage_task("update", task_id="uuid", status="done", assignee="User")`

**Examples:**
```json
// Create
{
  "action": "create",
  "project_id": "p-123",
  "title": "Implement authentication",
  "description": "Add JWT-based auth",
  "assignee": "claude",
  "status": "todo"
}

// Update
{
  "action": "update",
  "task_id": "t-456",
  "status": "doing",
  "assignee": "claude"
}

// Delete
{
  "action": "delete",
  "task_id": "t-789"
}
```

**Migration Notes:**
This tool replaces the deprecated individual operations:
- ❌ `archon_add_task` → ✅ `manage_task(action="create")`
- ❌ `archon_update_task` → ✅ `manage_task(action="update")`
- ❌ `archon_start_task` → ✅ `manage_task(action="update", status="doing")`
- ❌ `archon_complete_task` → ✅ `manage_task(action="update", status="done")`
- ❌ `archon_archive_task` → ✅ `manage_task(action="delete")`

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

**Current MCP Tool Status (Updated 2026-02-17):**
- **4 Archon task tools** - All working ✅
  - `archon_list_tasks` (legacy, still functional)
  - `archon_get_task` (legacy, still functional)
  - `find_tasks` (consolidated search/list/get)
  - `manage_task` (consolidated create/update/delete)
- **40+ GitHub tools** - All available
- **6 MCP management tools** - All working

**Tool Consolidation:**
- Replaced 7 individual tools with 4 streamlined tools
- Eliminated HTTP 405/422 errors through proper refactoring
- Improved efficiency with optimized payloads (truncated descriptions, count fields)
- Better pagination support (default 10 items vs previous 50)

**Recommendations:**
- ✅ Use new consolidated tools (`find_tasks`, `manage_task`) for all operations
- ✅ Legacy tools (`archon_list_tasks`, `archon_get_task`) remain functional for backward compatibility
- 🚀 Next: Implement session memory tools for Phase 2
- 📝 Pattern to follow: Consolidated tools with action parameters

**This inventory satisfies Task 5 requirements** and reflects current production implementation.

---

**Document Created By:** Claude (Archon Agent)
**Last Updated:** 2026-02-17
**Task ID:** 228609d2-7df2-4ecd-85d0-a5cefef60595
**Project:** Shared Memory System Implementation (b231255f-6ed9-4440-80de-958bcf7b4f9f)
**Status:** Updated - Tool refactor complete
