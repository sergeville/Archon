# Using Archon to Build Archon: Shared Memory Project Guide

## Overview

This guide shows how to use Archon's own project management system to track the implementation of the Shared Memory System. This is "dogfooding" - using Archon to improve itself!

## Why This Approach?

1. **Real-world Testing**: Test Archon's project management while building
2. **Multi-Agent Collaboration**: Multiple agents can work on different tasks
3. **Knowledge Integration**: All documentation stored in Archon's knowledge base
4. **Task Tracking**: Use Archon's task system to track progress
5. **Pattern Learning**: Harvest patterns while building (meta!)

## Setup Instructions

### Step 1: Load the Project into Archon

```bash
# Navigate to Archon directory
cd ~/Documents/Projects/Archon

# Make sure Archon is running
docker compose ps

# Load the project SQL
psql $SUPABASE_URL -f migration/shared_memory_project.sql
```

**What this does:**
- Creates 1 project: "Shared Memory System Implementation"
- Creates 60+ tasks organized by phase (Week 1-6)
- Sets up task dependencies and metadata
- Assigns all tasks to 'claude' initially (can be reassigned)

### Step 2: Verify Project in Archon UI

1. Open Archon UI: http://localhost:3737
2. Navigate to **Projects**
3. Find "Shared Memory System Implementation"
4. Click to view details

**You should see:**
- 6 features (phases)
- 60+ tasks organized by week
- Task metadata with acceptance criteria
- Tags for filtering

### Step 3: Connect Claude Code to Archon MCP

If not already connected:

1. Check MCP health: `curl http://localhost:8051/health`
2. Configure Claude Code with Archon MCP endpoint
3. Test connection: Use `find_projects` tool to see the new project

## Using Archon MCP Tools to Work on Tasks

### Finding Tasks

```python
# List all tasks for the project
find_tasks(filter_by="project", filter_value="<project-id>")

# Find tasks by phase
find_tasks(query="phase-1")

# Find tasks by status
find_tasks(filter_by="status", filter_value="todo")

# Find tasks for current week
find_tasks(query="week-1")
```

### Working on a Task

```python
# 1. Get task details
task = find_tasks(task_id="<task-id>")

# 2. Start work (mark as 'doing')
manage_task("update", task_id="<task-id>", status="doing")

# 3. Research if needed
rag_search_knowledge_base(query="MCP server implementation", match_count=5)

# 4. Do the work...
# (write code, create files, etc.)

# 5. Mark complete
manage_task("update", task_id="<task-id>", status="done")

# 6. Move to next task
find_tasks(filter_by="status", filter_value="todo")
```

### Multi-Agent Collaboration

```python
# Agent 1 (Claude) starts a task
manage_task("update", task_id="<task-id>", status="doing", assignee="claude")

# Agent 1 works and gets blocked
# Leave note in shared context (once Phase 4 is built)
write_shared_context(
  key="task_<task-id>_status",
  value={"status": "blocked", "blocker": "need schema review", "progress": "60%"},
  updated_by="claude"
)

# Agent 2 (Gemini) picks up
read_shared_context(key="task_<task-id>_status")
# Sees blocker, can help or wait

# Agent 1 unblocks and completes
manage_task("update", task_id="<task-id>", status="done")
```

## Task Organization

### By Phase (Feature)

Tasks are organized into 6 phases matching the 6-week plan:

- **Phase 1**: MCP Connection & Validation (Week 1)
- **Phase 2**: Session Memory & Semantic Search (Week 2)
- **Phase 3**: Pattern Learning System (Week 3)
- **Phase 4**: Multi-Agent Collaboration (Week 4)
- **Phase 5**: Optimization & Analytics (Week 5)
- **Phase 6**: Integration & Documentation (Week 6)

### By Tags

All tasks are tagged for easy filtering:

- `phase-1` through `phase-6`
- `week-1` through `week-6`
- `setup`, `testing`, `documentation`, `mcp`, `database`, etc.
- `unit-tests`, `integration`, `e2e`, `performance`

### By Status

- `todo`: Not started
- `doing`: Currently working on
- `review`: Ready for review
- `done`: Completed

### Task Order

Tasks have `task_order` field (100 down to 1):
- Higher number = higher priority
- Dependencies noted in metadata

## Storing Documentation in Archon

### Upload Implementation Docs

```bash
# In Archon UI
1. Go to Knowledge Base
2. Click "Upload Document"
3. Upload these files:
   - shared_memory_project.sql
   - Complete Implementation Plan (the main plan document)
   - Test Strategy
   - Architecture diagrams (when created)
```

### Crawl Reference Documentation

```bash
# In Archon UI
1. Go to Knowledge Base
2. Click "Crawl Website"
3. Add these URLs:
   - MCP specification docs
   - pgvector documentation
   - FastAPI docs
   - Supabase docs
```

### Search Documentation While Working

```python
# Find relevant docs
rag_search_knowledge_base(query="pgvector semantic search", match_count=3)

# Get specific document
rag_get_available_sources()  # List all sources
rag_search_knowledge_base(query="MCP tools", source_id="<source-id>")
```

## Workflow Examples

### Example 1: Start Phase 1

```python
# 1. Find all Phase 1 tasks
tasks = find_tasks(query="phase-1 week-1")

# 2. Start with first task
first_task = find_tasks(task_id="<check-health-task-id>")
manage_task("update", task_id=first_task.id, status="doing")

# 3. Execute the task
# Check: curl http://localhost:8051/health

# 4. Document results
# (Add notes to task or create document)

# 5. Mark complete
manage_task("update", task_id=first_task.id, status="done")

# 6. Harvest pattern (meta!)
harvest_pattern(
  pattern_type="success",
  domain="archon-development",
  description="How to verify Archon MCP server health",
  context={"service": "MCP server", "port": 8051},
  action="Use curl http://localhost:8051/health to check if server is healthy",
  created_by="claude"
)
```

### Example 2: Multi-Agent Task Split

```python
# Claude works on database schema
claude_task = find_tasks(query="Create agent_sessions Database Schema")
manage_task("update", task_id=claude_task.id, status="doing", assignee="claude")

# Gemini works on documentation
gemini_task = find_tasks(query="Document Current MCP Tool Inventory")
manage_task("update", task_id=gemini_task.id, status="doing", assignee="gemini")

# Both work independently
# Both can share learnings via patterns
```

### Example 3: Using Shared Context (Phase 4+)

```python
# Week 1: Track overall progress
write_shared_context(
  key="shared_memory_project_status",
  value={
    "current_phase": "Phase 1",
    "current_week": 1,
    "tasks_completed": 5,
    "tasks_remaining": 55,
    "blockers": [],
    "next_milestone": "Complete MCP connection validation"
  },
  priority=10,
  updated_by="claude"
)

# Any agent can check project status
status = read_shared_context(key="shared_memory_project_status")
print(f"Project is in {status['current_phase']}, Week {status['current_week']}")
```

## Progress Tracking

### Daily Check-in

```python
# Morning: See what's in progress
active_tasks = find_tasks(filter_by="status", filter_value="doing")

# End of day: Update progress
for task in active_tasks:
    # Update task with progress notes
    manage_task("update",
                task_id=task.id,
                metadata={
                    **task.metadata,
                    "daily_progress": "Completed X, blocked by Y"
                })
```

### Weekly Review

```python
# See completed tasks this week
completed = find_tasks(query="week-1 done")

# See remaining tasks
remaining = find_tasks(query="week-1 todo")

# Calculate progress
progress = len(completed) / (len(completed) + len(remaining))
print(f"Week 1 is {progress*100}% complete")
```

### Phase Completion

```python
# When phase is done
find_tasks(query="phase-1")  # Check all tasks done

# Document lessons learned
# Upload phase completion report to knowledge base

# Harvest patterns learned during phase
harvest_pattern(
  pattern_type="success",
  domain="project-management",
  description="How to complete a phase successfully",
  context={"phase": "Phase 1", "tasks": 12, "duration": "1 week"},
  action="Break phase into daily tasks, track progress daily, document blockers immediately",
  created_by="claude"
)
```

## Integration with Development Workflow

### Git Commits Reference Tasks

```bash
# In commit messages
git commit -m "Implement memory_service.py - Archon Task #89"

# This creates traceability between code and tasks
```

### Pull Requests Link to Tasks

```markdown
## Archon Task

This PR implements:
- Task #89: Create memory_service.py Backend Service
- Task #90: Integrate Embedding Generation

## Changes
- Added memory_service.py with all session management functions
- Integrated with existing embedding service
- Added unit tests with >90% coverage

## Testing
See Archon task acceptance criteria - all met.
```

### Documentation Updates

When creating docs, upload to Archon knowledge base:

1. Write the doc (e.g., `docs/mcp_tools_reference.md`)
2. Upload to Archon via UI or API
3. Reference in task completion
4. Now searchable via RAG for future work

## Success Metrics

Track these via Archon:

```python
# Tasks completed per week
tasks_by_week = {}
for week in range(1, 7):
    completed = find_tasks(query=f"week-{week} done")
    tasks_by_week[week] = len(completed)

# Patterns harvested
patterns = search_patterns(query="archon-development")
print(f"Harvested {len(patterns)} patterns during development")

# Agent collaboration
# (Track via shared_context_history once Phase 4 is built)
```

## Troubleshooting

### Can't See Project

```python
# Check if project exists
projects = find_projects(query="Shared Memory")

# If not found, re-run SQL
# psql $SUPABASE_URL -f migration/shared_memory_project.sql
```

### Tasks Not Showing

```python
# Check task count
tasks = find_tasks(filter_by="project", filter_value="<project-id>")
print(f"Found {len(tasks)} tasks")

# Should be 60+
```

### MCP Tools Not Working

```bash
# Check MCP server
curl http://localhost:8051/health

# Check tools list
curl http://localhost:8051/tools | jq '.tools[] | .name'

# Restart MCP server
docker compose restart archon-mcp
```

## Best Practices

1. **Start Each Day**: Check active tasks, review blockers
2. **Update Frequently**: Mark tasks as you work, don't batch
3. **Harvest Patterns**: When you learn something, save it
4. **Document Decisions**: Use shared context for important decisions
5. **Review Weekly**: Check progress, adjust priorities
6. **Use Search**: RAG search for similar past work
7. **Collaborate**: Use shared context to coordinate with other agents

## Next Steps

1. Run the SQL to create the project
2. View it in Archon UI
3. Start with Phase 1, Day 1 tasks
4. Use MCP tools to track progress
5. Harvest patterns as you learn
6. Build the shared memory system while using Archon to track it!

---

**This is meta-learning at its finest**: Using Archon to build Archon's shared memory system, while learning how to use shared memory systems, while improving Archon's ability to track complex projects. 🚀

The patterns you harvest while building this will become part of Archon's knowledge base, making it smarter for the next project!
