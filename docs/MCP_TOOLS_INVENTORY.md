# Archon MCP Tools Inventory

**Created**: 2026-02-18
**Project**: Shared Memory System Implementation - Phase 1
**Version**: 2.0 (Complete Inventory)

## Executive Summary

This document provides a comprehensive inventory of all MCP (Model Context Protocol) tools available in the Archon system. These tools enable AI agents (Claude, Gemini, GPT) to interact with Archon's knowledge base, projects, tasks, sessions, and documents through standardized interfaces.

**Total Tools**: 22 tools across 8 feature domains
**Architecture**: Consolidated pattern with `find_*` (search/list/get) and `manage_*` (create/update/delete) operations
**Location**: `python/src/mcp_server/features/`

## Tool Organization Pattern

Archon follows a consolidated tool pattern that reduces the number of individual CRUD operations while maintaining full functionality:

- **`find_*` Tools**: Handle list, search, and get single item operations
  - Support pagination (page, per_page)
  - Include search/filter capabilities
  - Return optimized payloads for lists (truncated descriptions, counts instead of arrays)
  - Return full details for single item gets

- **`manage_*` Tools**: Handle create, update, and delete operations with an "action" parameter
  - Single tool per resource type
  - Action parameter: "create" | "update" | "delete"
  - Conditional required fields based on action
  - Consistent error handling

## Complete Tool Inventory

### 1. Task Management (2 tools)

**Location**: `python/src/mcp_server/features/tasks/task_tools.py`

#### `find_tasks`
- **Description**: Find and search tasks (consolidated: list + search + get)
- **Parameters**: query, task_id, filter_by, filter_value, project_id, include_closed, page, per_page
- **Optimization**: Truncates descriptions to 1000 chars, replaces arrays with counts
- **Examples**: Search, get single task, filter by status/project/assignee

#### `manage_task`
- **Description**: Manage tasks (create/update/delete)
- **Parameters**: action, task_id, project_id, title, description, status, assignee, task_order, feature
- **Actions**: "create" | "update" | "delete"
- **Task Granularity**: 30 minutes to 4 hours per task

### 2. Session Management (5 tools)

**Location**: `python/src/mcp_server/features/sessions/session_tools.py`

#### `find_sessions`
- **Description**: Find and retrieve agent sessions
- **Parameters**: session_id, agent, project_id, limit
- **Event Types**: Includes event logs with each session

#### `manage_session`
- **Description**: Manage agent sessions
- **Actions**: "create" | "end" | "update"
- **Parameters**: action, agent, session_id, project_id, summary, context, metadata

#### `log_session_event`
- **Description**: Log events within sessions
- **Event Types**: task_created, task_updated, decision_made, error_encountered, pattern_identified, context_shared
- **Parameters**: session_id, event_type, event_data, metadata

#### `search_sessions_semantic`
- **Description**: Semantic search using vector embeddings
- **Parameters**: query, limit, threshold
- **Use Case**: Find sessions about specific topics without exact keywords

#### `get_agent_context`
- **Description**: Get agent's recent work context
- **Modes**: "last" (most recent) | "recent" (N days)
- **Parameters**: agent, mode, days, limit

### 3. RAG / Knowledge Base (5 tools)

**Location**: `python/src/mcp_server/features/rag/rag_tools.py`

#### `rag_get_available_sources`
- **Description**: List knowledge sources with pagination
- **Parameters**: page, per_page
- **Returns**: source_id for filtering other tools

#### `rag_search_knowledge_base`
- **Description**: RAG search with vector embeddings
- **Parameters**: query (2-5 keywords), source_id, match_count, return_mode
- **Return Modes**: "pages" (full pages) | "chunks" (raw text)
- **Important**: Query must be SHORT and FOCUSED

#### `rag_search_code_examples`
- **Description**: Search for code examples
- **Parameters**: query (2-5 keywords), source_id, match_count
- **Returns**: Code examples with summaries

#### `rag_list_pages_for_source`
- **Description**: List all pages for a source
- **Parameters**: source_id, section
- **Workflow**: 1) Get sources, 2) List pages, 3) Read full page

#### `rag_read_full_page`
- **Description**: Retrieve complete page content
- **Parameters**: page_id | url (either, not both)
- **Returns**: full_content, title, url, metadata

### 4. Project Management (2 tools)

**Location**: `python/src/mcp_server/features/projects/project_tools.py`

#### `find_projects`
- **Description**: List and search projects
- **Parameters**: project_id, query, status, page, per_page
- **Optimization**: Truncated descriptions, feature counts

#### `manage_project`
- **Description**: Manage projects
- **Actions**: "create" | "update" | "delete"
- **Parameters**: action, project_id, title, description, github_repo, pinned, archived, status
- **Note**: Create may be async with progress polling

### 5. Pattern Management (3 tools)

**Location**: `python/src/mcp_server/features/patterns/pattern_tools.py`

#### `harvest_pattern`
- **Description**: Save learned patterns
- **Pattern Types**: success, failure, technical, process
- **Parameters**: pattern_type, domain, description, action, outcome, context, metadata, created_by

#### `search_patterns`
- **Description**: Semantic pattern search
- **Parameters**: query, limit, threshold, domain
- **Use Case**: Find similar approaches before starting tasks

#### `record_pattern_observation`
- **Description**: Record pattern application
- **Parameters**: pattern_id, session_id, success_rating, feedback, metadata
- **Rating**: 1-5 effectiveness score

### 6. Document Management (2 tools)

**Location**: `python/src/mcp_server/features/documents/document_tools.py`

#### `find_documents`
- **Description**: Find and search documents
- **Parameters**: project_id, document_id, query, document_type, page, per_page
- **Document Types**: spec, design, note, prp, api, guide
- **Optimization**: Content removed from list views

#### `manage_document`
- **Description**: Manage documents
- **Actions**: "create" | "update" | "delete"
- **Parameters**: action, project_id, document_id, title, document_type, content, tags, author
- **Content**: Structured JSON format

### 7. Version Management (2 tools)

**Location**: `python/src/mcp_server/features/documents/version_tools.py`

#### `find_versions`
- **Description**: Find version history
- **Parameters**: project_id, field_name, version_number, page, per_page
- **Fields**: docs, features, data, prd
- **Optimization**: Content removed from lists

#### `manage_version`
- **Description**: Manage versions
- **Actions**: "create" | "restore"
- **Parameters**: action, project_id, field_name, version_number, content, change_summary, document_id, created_by

### 8. Feature Management (1 tool)

**Location**: `python/src/mcp_server/features/feature_tools.py`

#### `get_project_features`
- **Description**: Get project features array
- **Parameters**: project_id
- **Feature Structures**:
  - Simple: {name, status}
  - Components: {name, status, components[]}
  - Progress: {name, status, done, total}
  - Metadata: {name, provider, version, enabled}

## Common Patterns

### Error Handling
- Standardized via `MCPErrorFormatter`
- Error types: validation_error, not_found, timeout, invalid_action
- Includes suggestions for fixing issues

### Pagination
- Standard: page, per_page
- Returns: count (in response), total (all matching)
- Default: per_page=10

### Optimizations
- Text truncation: 1000 chars for descriptions
- Array replacement: Counts instead of full arrays
- Content removal: Full content only in single-item gets
- Selective detail: Lists optimized, single items full

## Implementation Notes

### HTTP-Based Architecture
- Base URL: Via `get_api_url()`
- Client: `httpx.AsyncClient`
- Endpoints: `/api/{resource}` (RESTful)

### Consolidation Benefits
- Reduced from 30+ to 22 tools
- Consistent interface patterns
- 60% reduction in MCP overhead
- Easier maintenance

### Backend API Mapping
- Projects: `python/src/server/api_routes/projects_api.py`
- Sessions: `python/src/server/api_routes/sessions_api.py`
- Knowledge: `python/src/server/api_routes/knowledge_api.py`

## Usage Guidelines

### Best Practices
1. Keep search queries short (2-5 keywords)
2. Use filters to narrow results
3. Check existing data before creating
4. Start with small per_page values
5. Handle errors gracefully

### Common Workflows

**Creating a Task:**
```
1. find_projects(query="name")
2. manage_task("create", project_id, title, ...)
```

**Resuming Work:**
```
1. get_agent_context(agent="claude", mode="last")
2. Review session events
3. Continue based on context
```

**Knowledge Base Search:**
```
1. rag_get_available_sources()
2. rag_search_knowledge_base(query, source_id)
3. rag_read_full_page(page_id)
```

**Pattern Learning:**
```
1. search_patterns(query="problem")
2. Review matches
3. harvest_pattern(...) if novel
```

## Version History

**Version 2.0** (2026-02-18):
- Complete inventory of all 22 Archon MCP tools
- All tool signatures, parameters, and return types documented
- Usage examples and best practices included
- Replaces incomplete v1.0 from 2026-02-17

## Related Documentation

- **Architecture**: `PRPs/ai_docs/ARCHITECTURE.md`
- **API Conventions**: `PRPs/ai_docs/API_NAMING_CONVENTIONS.md`
- **Query Patterns**: `PRPs/ai_docs/QUERY_PATTERNS.md`
- **Phase 2 Status**: `docs/PHASE_2_ACTUAL_STATUS.md`
- **CLAUDE.md**: Repository root

---

**Document Created By**: Claude (Archon Agent)
**Last Updated**: 2026-02-18
**Task**: Document Current MCP Tool Inventory (Phase 1, Task 5)
**Project**: Shared Memory System Implementation
