-- ============================================================================
-- ARCHON PROJECT: SHARED MEMORY SYSTEM IMPLEMENTATION
-- ============================================================================
-- This script creates a complete Archon project to track the implementation
-- of the shared memory system using Archon's own project management.
--
-- This is "dogfooding" - using Archon to build Archon's features!
-- ============================================================================

-- Create the main project
INSERT INTO archon_projects (
  id,
  title,
  description,
  status,
  priority,
  features,
  metadata
) VALUES (
  gen_random_uuid(),
  'Shared Memory System Implementation',
  'Implement a production-ready shared memory system for multi-agent collaboration, enabling working/short-term/long-term memory layers, pattern learning, and agent coordination. This brings Archon to 100% alignment with industry standards (Eion, MeshOS, Pantheon).',
  'active',
  'high',
  ARRAY[
    'Phase 1: MCP Connection & Validation',
    'Phase 2: Session Memory & Semantic Search',
    'Phase 3: Pattern Learning System',
    'Phase 4: Multi-Agent Collaboration',
    'Phase 5: Optimization & Analytics',
    'Phase 6: Integration & Documentation'
  ],
  jsonb_build_object(
    'timeline', '6 weeks',
    'effort_hours', '120-150',
    'team_size', '1-2 developers',
    'alignment_target', '100%',
    'current_completion', '82-85%',
    'risk_level', 'Low',
    'technologies', ARRAY['PostgreSQL', 'pgvector', 'FastAPI', 'MCP', 'Python', 'React'],
    'references', ARRAY['Eion', 'MeshOS', 'Pantheon', 'MCP Standard']
  )
) RETURNING id AS project_id;

-- Store the project_id for task creation
-- Note: In practice, you'd capture this ID and use it below
-- For this script, we'll use a CTE

WITH project AS (
  SELECT id FROM archon_projects WHERE title = 'Shared Memory System Implementation'
)

-- ============================================================================
-- PHASE 1: MCP Connection & Validation (Week 1)
-- ============================================================================

-- Phase 1: Day 1-2 Tasks
INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Check Archon MCP Server Health',
  'Verify Archon MCP server is running and healthy. Test endpoint: curl http://localhost:8051/health. Expected response: {"success":true,"health":{"status":"healthy"}}',
  'todo',
  'claude',
  100,
  jsonb_build_object(
    'phase', 'Phase 1',
    'week', 1,
    'day', '1-2',
    'estimated_hours', 0.5,
    'acceptance_criteria', ARRAY[
      'MCP server responds with 200 OK',
      'Health endpoint returns healthy status',
      'No connection errors in logs'
    ]
  ),
  ARRAY['phase-1', 'setup', 'mcp', 'week-1']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Verify All Archon Services Running',
  'Check that all Archon Docker services are running: archon-server, archon-mcp, archon-ui, archon-agents. Use docker compose ps to verify.',
  'todo',
  'claude',
  99,
  jsonb_build_object(
    'phase', 'Phase 1',
    'week', 1,
    'day', '1-2',
    'estimated_hours', 0.5,
    'acceptance_criteria', ARRAY[
      'All 4 core services running',
      'No services in restart loop',
      'All health endpoints responding'
    ]
  ),
  ARRAY['phase-1', 'setup', 'docker', 'week-1']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Configure Claude Code MCP Connection',
  'Add Archon MCP server configuration to Claude Code. Update configuration to point to http://localhost:8051/sse for MCP connection.',
  'todo',
  'claude',
  98,
  jsonb_build_object(
    'phase', 'Phase 1',
    'week', 1,
    'day', '1-2',
    'estimated_hours', 1,
    'acceptance_criteria', ARRAY[
      'Claude Code configuration updated',
      'MCP connection established',
      'Tools list retrieved successfully'
    ],
    'blocked_by', 'Check Archon MCP Server Health'
  ),
  ARRAY['phase-1', 'setup', 'mcp', 'configuration', 'week-1']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Test Existing MCP Tools from Claude Code',
  'Test at least 5 existing Archon MCP tools: rag_search_knowledge_base, find_tasks, manage_task, find_projects, rag_get_available_sources. Document response times and success rates.',
  'todo',
  'claude',
  97,
  jsonb_build_object(
    'phase', 'Phase 1',
    'week', 1,
    'day', '1-2',
    'estimated_hours', 2,
    'acceptance_criteria', ARRAY[
      'All 5 tools execute successfully',
      'Response times <500ms',
      'No authentication errors',
      'Results match expected format'
    ],
    'blocked_by', 'Configure Claude Code MCP Connection'
  ),
  ARRAY['phase-1', 'testing', 'mcp', 'validation', 'week-1']
FROM project;

-- Phase 1: Day 3-4 Tasks
INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Document Current MCP Tool Inventory',
  'Create comprehensive list of all existing MCP tools in python/src/mcp_server/features/. Document tool signatures, parameters, return types, and usage examples.',
  'todo',
  'claude',
  96,
  jsonb_build_object(
    'phase', 'Phase 1',
    'week', 1,
    'day', '3-4',
    'estimated_hours', 3,
    'deliverable', 'docs/mcp_tools_inventory.md',
    'acceptance_criteria', ARRAY[
      'All tools documented',
      'Examples provided for each tool',
      'Parameter types specified',
      'Return formats documented'
    ]
  ),
  ARRAY['phase-1', 'documentation', 'mcp', 'week-1']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Map Existing Tools to Memory Layers',
  'Create mapping showing which existing Archon features correspond to the 3-layer memory model: Working Memory (current context), Short-Term Memory (archon_tasks), Long-Term Memory (documents/RAG).',
  'todo',
  'claude',
  95,
  jsonb_build_object(
    'phase', 'Phase 1',
    'week', 1,
    'day', '3-4',
    'estimated_hours', 2,
    'deliverable', 'docs/memory_layer_mapping.md',
    'acceptance_criteria', ARRAY[
      'All 3 memory layers mapped',
      'Gaps identified',
      'Current capabilities documented',
      'Missing features listed'
    ]
  ),
  ARRAY['phase-1', 'analysis', 'architecture', 'week-1']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Create Baseline Performance Metrics',
  'Measure and document current system performance: MCP response times, database query performance, tool success rates, concurrent request handling.',
  'todo',
  'claude',
  94,
  jsonb_build_object(
    'phase', 'Phase 1',
    'week', 1,
    'day', '3-4',
    'estimated_hours', 3,
    'deliverable', 'docs/baseline_metrics.md',
    'acceptance_criteria', ARRAY[
      'Response time p50/p95/p99 measured',
      'Database query performance logged',
      'Concurrent request test completed',
      'Baseline documented for comparison'
    ]
  ),
  ARRAY['phase-1', 'performance', 'metrics', 'week-1']
FROM project;

-- Phase 1: Day 5 Tasks
INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Test Multi-Agent Scenario',
  'Connect a second agent (Gemini or Cursor) to Archon MCP. Verify both agents can access same knowledge base concurrently. Test concurrent task access and document collaboration limitations.',
  'todo',
  'claude',
  93,
  jsonb_build_object(
    'phase', 'Phase 1',
    'week', 1,
    'day', '5',
    'estimated_hours', 4,
    'deliverable', 'docs/multi_agent_test_results.md',
    'acceptance_criteria', ARRAY[
      '2+ agents connected simultaneously',
      'Both can access same knowledge base',
      'Concurrent task access tested',
      'Limitations documented',
      'No data corruption'
    ]
  ),
  ARRAY['phase-1', 'testing', 'multi-agent', 'week-1']
FROM project;

-- ============================================================================
-- PHASE 2: Session Memory & Semantic Search (Week 2)
-- ============================================================================

-- Phase 2: Day 1 Tasks
INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Create agent_sessions Database Schema',
  'Create agent_sessions table with columns: id, agent_name, session_id, started_at, ended_at, context, metadata. Add appropriate indexes.',
  'todo',
  'claude',
  92,
  jsonb_build_object(
    'phase', 'Phase 2',
    'week', 2,
    'day', '1',
    'estimated_hours', 1,
    'deliverable', 'migration/002_agent_sessions.sql',
    'acceptance_criteria', ARRAY[
      'Table created successfully',
      'All indexes added',
      'Foreign key constraints valid',
      'Sample data inserted for testing'
    ]
  ),
  ARRAY['phase-2', 'database', 'schema', 'week-2']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Create conversation_history with Vector Embeddings',
  'Create conversation_history table with columns: id, session_id, role, message, tools_used, type, subtype, embedding (VECTOR(1536)), created_at, metadata. Add pgvector indexes.',
  'todo',
  'claude',
  91,
  jsonb_build_object(
    'phase', 'Phase 2',
    'week', 2,
    'day', '1',
    'estimated_hours', 2,
    'deliverable', 'migration/003_conversation_history.sql',
    'acceptance_criteria', ARRAY[
      'Table with vector column created',
      'ivfflat index added for embeddings',
      'Trigger placeholder created',
      'MeshOS taxonomy fields included',
      'Test queries run successfully'
    ]
  ),
  ARRAY['phase-2', 'database', 'schema', 'semantic-search', 'week-2']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Test Schema with Sample Data',
  'Insert sample session and conversation data. Test all indexes. Verify foreign key constraints. Test semantic search queries.',
  'todo',
  'claude',
  90,
  jsonb_build_object(
    'phase', 'Phase 2',
    'week', 2,
    'day', '1',
    'estimated_hours', 1,
    'acceptance_criteria', ARRAY[
      'Sample data inserted',
      'All queries execute <200ms',
      'Foreign keys enforced',
      'Indexes used in query plans'
    ],
    'blocked_by', 'Create conversation_history with Vector Embeddings'
  ),
  ARRAY['phase-2', 'testing', 'database', 'week-2']
FROM project;

-- Phase 2: Day 2-3 Tasks
INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Create memory_service.py Backend Service',
  'Implement memory service in python/src/server/services/memory_service.py with functions: create_session, end_session, store_message, get_session_history, search_conversations.',
  'todo',
  'claude',
  89,
  jsonb_build_object(
    'phase', 'Phase 2',
    'week', 2,
    'day', '2-3',
    'estimated_hours', 6,
    'deliverable', 'python/src/server/services/memory_service.py',
    'acceptance_criteria', ARRAY[
      'All 5 functions implemented',
      'Type hints added',
      'Error handling included',
      'Docstrings written',
      'Unit tests pass'
    ]
  ),
  ARRAY['phase-2', 'backend', 'service', 'week-2']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Integrate Embedding Generation',
  'Add embedding generation to conversation storage. Use existing Archon embedding service. Update store_message to auto-generate embeddings for semantic search.',
  'todo',
  'claude',
  88,
  jsonb_build_object(
    'phase', 'Phase 2',
    'week', 2,
    'day', '2-3',
    'estimated_hours', 3,
    'acceptance_criteria', ARRAY[
      'Embedding service integrated',
      'Auto-embedding on message insert',
      'Vector similarity search working',
      'Performance acceptable (<500ms)'
    ],
    'blocked_by', 'Create memory_service.py Backend Service'
  ),
  ARRAY['phase-2', 'backend', 'embeddings', 'semantic-search', 'week-2']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Write Unit Tests for Memory Service',
  'Create comprehensive unit tests in python/tests/server/services/test_memory_service.py. Test all functions, error cases, edge cases.',
  'todo',
  'claude',
  87,
  jsonb_build_object(
    'phase', 'Phase 2',
    'week', 2,
    'day', '2-3',
    'estimated_hours', 3,
    'deliverable', 'python/tests/server/services/test_memory_service.py',
    'acceptance_criteria', ARRAY[
      '>90% code coverage',
      'All edge cases tested',
      'Error handling verified',
      'All tests pass'
    ],
    'blocked_by', 'Create memory_service.py Backend Service'
  ),
  ARRAY['phase-2', 'testing', 'unit-tests', 'week-2']
FROM project;

-- Phase 2: Day 4 Tasks
INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Implement Memory MCP Tools',
  'Create MCP tools in python/src/mcp_server/features/memory/memory_tools.py: create_session, end_session, store_conversation_message, get_session_history, search_conversation_history.',
  'todo',
  'claude',
  86,
  jsonb_build_object(
    'phase', 'Phase 2',
    'week', 2,
    'day', '4',
    'estimated_hours', 4,
    'deliverable', 'python/src/mcp_server/features/memory/memory_tools.py',
    'acceptance_criteria', ARRAY[
      'All 5 tools implemented',
      'MCP tool schema defined',
      'Error handling added',
      'Tools registered in MCP server'
    ],
    'blocked_by', 'Create memory_service.py Backend Service'
  ),
  ARRAY['phase-2', 'mcp', 'tools', 'week-2']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Register Memory Tools in MCP Server',
  'Update python/src/mcp_server/features/memory/__init__.py to register all memory tools. Test tool discovery via MCP.',
  'todo',
  'claude',
  85,
  jsonb_build_object(
    'phase', 'Phase 2',
    'week', 2,
    'day', '4',
    'estimated_hours', 1,
    'acceptance_criteria', ARRAY[
      'Tools appear in MCP tool list',
      'Tool metadata correct',
      'Test execution succeeds'
    ],
    'blocked_by', 'Implement Memory MCP Tools'
  ),
  ARRAY['phase-2', 'mcp', 'registration', 'week-2']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Write Integration Tests for Memory MCP Tools',
  'Create integration tests in python/tests/mcp_server/features/test_memory_tools.py. Test all tools end-to-end.',
  'todo',
  'claude',
  84,
  jsonb_build_object(
    'phase', 'Phase 2',
    'week', 2,
    'day', '4',
    'estimated_hours', 3,
    'deliverable', 'python/tests/mcp_server/features/test_memory_tools.py',
    'acceptance_criteria', ARRAY[
      'All tools tested',
      'Error cases covered',
      'Integration validated',
      'All tests pass'
    ],
    'blocked_by', 'Implement Memory MCP Tools'
  ),
  ARRAY['phase-2', 'testing', 'integration', 'week-2']
FROM project;

-- Phase 2: Day 5 Tasks
INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Create Memory API Routes (Optional)',
  'Add memory API routes in python/src/server/api_routes/memory_api.py for direct HTTP access to memory functions.',
  'todo',
  'claude',
  83,
  jsonb_build_object(
    'phase', 'Phase 2',
    'week', 2,
    'day', '5',
    'estimated_hours', 2,
    'deliverable', 'python/src/server/api_routes/memory_api.py',
    'acceptance_criteria', ARRAY[
      'RESTful endpoints created',
      'OpenAPI docs generated',
      'Error handling consistent',
      'CORS configured'
    ]
  ),
  ARRAY['phase-2', 'backend', 'api', 'optional', 'week-2']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Test Memory API via HTTP',
  'Test all memory API endpoints using curl/Postman. Verify response formats, error handling, authentication.',
  'todo',
  'claude',
  82,
  jsonb_build_object(
    'phase', 'Phase 2',
    'week', 2,
    'day', '5',
    'estimated_hours', 1,
    'acceptance_criteria', ARRAY[
      'All endpoints tested',
      'Response format validated',
      'Error codes correct',
      'Documentation updated'
    ],
    'blocked_by', 'Create Memory API Routes (Optional)'
  ),
  ARRAY['phase-2', 'testing', 'api', 'week-2']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Validate Phase 2 Success Criteria',
  'Run validation checklist: conversation persists across restarts, semantic search works (recall@5 >0.7), session history queryable for 7 days, 50+ messages stored.',
  'todo',
  'claude',
  81,
  jsonb_build_object(
    'phase', 'Phase 2',
    'week', 2,
    'day', '5',
    'estimated_hours', 2,
    'deliverable', 'docs/phase2_validation_report.md',
    'acceptance_criteria', ARRAY[
      'Conversation persistence verified',
      'Semantic search recall >0.7',
      'Session history works',
      '50+ messages test completed',
      'All criteria met'
    ]
  ),
  ARRAY['phase-2', 'validation', 'testing', 'week-2']
FROM project;

-- ============================================================================
-- PHASE 3: Pattern Learning System (Week 3)
-- ============================================================================

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Create learned_patterns Database Schema',
  'Create learned_patterns table with vector embeddings, confidence scoring, MeshOS taxonomy, and pattern metadata.',
  'todo',
  'claude',
  80,
  jsonb_build_object(
    'phase', 'Phase 3',
    'week', 3,
    'day', '1',
    'estimated_hours', 2,
    'deliverable', 'migration/004_learned_patterns.sql'
  ),
  ARRAY['phase-3', 'database', 'schema', 'week-3']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Create pattern_feedback Table',
  'Create pattern_feedback table and confidence update trigger for Bayesian confidence calculation.',
  'todo',
  'claude',
  79,
  jsonb_build_object(
    'phase', 'Phase 3',
    'week', 3,
    'day', '1',
    'estimated_hours', 2,
    'deliverable', 'migration/005_pattern_feedback.sql'
  ),
  ARRAY['phase-3', 'database', 'schema', 'week-3']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Test Pattern Schema with Sample Data',
  'Insert sample patterns, test confidence triggers, verify semantic search on patterns.',
  'todo',
  'claude',
  78,
  jsonb_build_object(
    'phase', 'Phase 3',
    'week', 3,
    'day', '1',
    'estimated_hours', 1
  ),
  ARRAY['phase-3', 'testing', 'database', 'week-3']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Create learning_service.py Backend Service',
  'Implement pattern harvesting, search, feedback, and confidence calculation functions.',
  'todo',
  'claude',
  77,
  jsonb_build_object(
    'phase', 'Phase 3',
    'week', 3,
    'day', '2-3',
    'estimated_hours', 6,
    'deliverable', 'python/src/server/services/learning_service.py'
  ),
  ARRAY['phase-3', 'backend', 'service', 'week-3']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Implement Semantic Pattern Search',
  'Add pgvector-based semantic search for patterns with confidence filtering and ranking.',
  'todo',
  'claude',
  76,
  jsonb_build_object(
    'phase', 'Phase 3',
    'week', 3,
    'day', '2-3',
    'estimated_hours', 3
  ),
  ARRAY['phase-3', 'backend', 'semantic-search', 'week-3']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Write Unit Tests for Learning Service',
  'Comprehensive tests for pattern service with >90% coverage.',
  'todo',
  'claude',
  75,
  jsonb_build_object(
    'phase', 'Phase 3',
    'week', 3,
    'day', '2-3',
    'estimated_hours', 3,
    'deliverable', 'python/tests/server/services/test_learning_service.py'
  ),
  ARRAY['phase-3', 'testing', 'unit-tests', 'week-3']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Implement Pattern MCP Tools',
  'Create MCP tools: harvest_pattern, search_patterns, report_pattern_success, report_pattern_failure, get_pattern_confidence.',
  'todo',
  'claude',
  74,
  jsonb_build_object(
    'phase', 'Phase 3',
    'week', 3,
    'day', '4',
    'estimated_hours', 4,
    'deliverable', 'python/src/mcp_server/features/learning/pattern_tools.py'
  ),
  ARRAY['phase-3', 'mcp', 'tools', 'week-3']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Test Pattern Harvesting Workflow',
  'End-to-end test of pattern learning: harvest, search, feedback, confidence update.',
  'todo',
  'claude',
  73,
  jsonb_build_object(
    'phase', 'Phase 3',
    'week', 3,
    'day', '4',
    'estimated_hours', 2
  ),
  ARRAY['phase-3', 'testing', 'integration', 'week-3']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Harvest 10 Test Patterns',
  'Manually harvest 10 real patterns from development work. Test semantic search quality.',
  'todo',
  'claude',
  72,
  jsonb_build_object(
    'phase', 'Phase 3',
    'week', 3,
    'day', '5',
    'estimated_hours', 2
  ),
  ARRAY['phase-3', 'validation', 'manual-testing', 'week-3']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Document Pattern Harvesting Best Practices',
  'Create guide for agents on when and how to harvest patterns effectively.',
  'todo',
  'claude',
  71,
  jsonb_build_object(
    'phase', 'Phase 3',
    'week', 3,
    'day', '5',
    'estimated_hours', 2,
    'deliverable', 'docs/pattern_harvesting_guide.md'
  ),
  ARRAY['phase-3', 'documentation', 'week-3']
FROM project;

-- ============================================================================
-- PHASE 4: Multi-Agent Collaboration (Week 4)
-- ============================================================================

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Create agent_registry Database Schema',
  'Create agent registry table for tracking active agents, capabilities, and status.',
  'todo',
  'claude',
  70,
  jsonb_build_object(
    'phase', 'Phase 4',
    'week', 4,
    'day', '1',
    'estimated_hours', 1,
    'deliverable', 'migration/006_agent_registry.sql'
  ),
  ARRAY['phase-4', 'database', 'schema', 'week-4']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Create shared_context Tables',
  'Create shared_context and shared_context_history tables with change tracking triggers.',
  'todo',
  'claude',
  69,
  jsonb_build_object(
    'phase', 'Phase 4',
    'week', 4,
    'day', '1',
    'estimated_hours', 2,
    'deliverable', 'migration/007_shared_context.sql'
  ),
  ARRAY['phase-4', 'database', 'schema', 'week-4']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Create agent_notifications Table',
  'Create notification system for agent-to-agent communication.',
  'todo',
  'claude',
  68,
  jsonb_build_object(
    'phase', 'Phase 4',
    'week', 4,
    'day', '1',
    'estimated_hours', 1,
    'deliverable', 'migration/008_agent_notifications.sql'
  ),
  ARRAY['phase-4', 'database', 'schema', 'week-4']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Test Collaboration Schema',
  'Test all triggers, constraints, and sample multi-agent scenarios.',
  'todo',
  'claude',
  67,
  jsonb_build_object(
    'phase', 'Phase 4',
    'week', 4,
    'day', '1',
    'estimated_hours', 1
  ),
  ARRAY['phase-4', 'testing', 'database', 'week-4']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Create collaboration_service.py',
  'Implement agent registry, shared context, and notification functions.',
  'todo',
  'claude',
  66,
  jsonb_build_object(
    'phase', 'Phase 4',
    'week', 4,
    'day', '2-3',
    'estimated_hours', 6,
    'deliverable', 'python/src/server/services/collaboration_service.py'
  ),
  ARRAY['phase-4', 'backend', 'service', 'week-4']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Implement Agent Registry MCP Tools',
  'Create tools: register_agent, update_agent_status, get_active_agents, heartbeat_agent.',
  'todo',
  'claude',
  65,
  jsonb_build_object(
    'phase', 'Phase 4',
    'week', 4,
    'day', '3-4',
    'estimated_hours', 3,
    'deliverable', 'python/src/mcp_server/features/collaboration/agent_tools.py'
  ),
  ARRAY['phase-4', 'mcp', 'tools', 'week-4']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Implement Shared Context MCP Tools',
  'Create tools: write_shared_context, read_shared_context, list_shared_context, delete_shared_context, get_context_history.',
  'todo',
  'claude',
  64,
  jsonb_build_object(
    'phase', 'Phase 4',
    'week', 4,
    'day', '3-4',
    'estimated_hours', 3,
    'deliverable', 'python/src/mcp_server/features/collaboration/context_tools.py'
  ),
  ARRAY['phase-4', 'mcp', 'tools', 'week-4']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Implement Notification MCP Tools',
  'Create tools: notify_agent, notify_all_agents, get_notifications, mark_notification_read.',
  'todo',
  'claude',
  63,
  jsonb_build_object(
    'phase', 'Phase 4',
    'week', 4,
    'day', '3-4',
    'estimated_hours', 2
  ),
  ARRAY['phase-4', 'mcp', 'tools', 'week-4']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Test Agent Handoff Scenario',
  'Test Claude starting task, writing context, Gemini picking up and completing.',
  'todo',
  'claude',
  62,
  jsonb_build_object(
    'phase', 'Phase 4',
    'week', 4,
    'day', '5',
    'estimated_hours', 2
  ),
  ARRAY['phase-4', 'testing', 'multi-agent', 'week-4']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Test Parallel Collaboration Scenario',
  'Test 3 agents working on different tasks concurrently with shared context.',
  'todo',
  'claude',
  61,
  jsonb_build_object(
    'phase', 'Phase 4',
    'week', 4,
    'day', '5',
    'estimated_hours', 2
  ),
  ARRAY['phase-4', 'testing', 'multi-agent', 'week-4']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Validate Phase 4 Success Criteria',
  'Verify 2+ agents collaborate, context updates visible, handoffs work, no conflicts.',
  'todo',
  'claude',
  60,
  jsonb_build_object(
    'phase', 'Phase 4',
    'week', 4,
    'day', '5',
    'estimated_hours', 2,
    'deliverable', 'docs/phase4_validation_report.md'
  ),
  ARRAY['phase-4', 'validation', 'testing', 'week-4']
FROM project;

-- ============================================================================
-- PHASE 5: Optimization & Analytics (Week 5)
-- ============================================================================

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Add Database Query Performance Logging',
  'Implement query performance monitoring and logging for optimization.',
  'todo',
  'claude',
  59,
  jsonb_build_object(
    'phase', 'Phase 5',
    'week', 5,
    'day', '1-2',
    'estimated_hours', 3
  ),
  ARRAY['phase-5', 'performance', 'logging', 'week-5']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Optimize Slow Queries',
  'Identify and optimize queries >200ms. Add indexes where needed.',
  'todo',
  'claude',
  58,
  jsonb_build_object(
    'phase', 'Phase 5',
    'week', 5,
    'day', '1-2',
    'estimated_hours', 4
  ),
  ARRAY['phase-5', 'performance', 'optimization', 'week-5']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Implement Caching Layer',
  'Add caching for frequently accessed data (patterns, shared context).',
  'todo',
  'claude',
  57,
  jsonb_build_object(
    'phase', 'Phase 5',
    'week', 5,
    'day', '1-2',
    'estimated_hours', 3
  ),
  ARRAY['phase-5', 'performance', 'caching', 'week-5']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Load Test with 100 Concurrent Requests',
  'Run load test with 100 concurrent MCP requests. Measure p95 latency.',
  'todo',
  'claude',
  56,
  jsonb_build_object(
    'phase', 'Phase 5',
    'week', 5,
    'day', '1-2',
    'estimated_hours', 2
  ),
  ARRAY['phase-5', 'performance', 'load-testing', 'week-5']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Create Archival Job for Old Conversations',
  'Implement job to archive conversations >7 days old.',
  'todo',
  'claude',
  55,
  jsonb_build_object(
    'phase', 'Phase 5',
    'week', 5,
    'day', '3',
    'estimated_hours', 3,
    'deliverable', 'python/src/server/jobs/archive_old_data.py'
  ),
  ARRAY['phase-5', 'maintenance', 'archival', 'week-5']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Create Cleanup Job for Old Notifications',
  'Implement job to remove read notifications >30 days old.',
  'todo',
  'claude',
  54,
  jsonb_build_object(
    'phase', 'Phase 5',
    'week', 5,
    'day', '3',
    'estimated_hours', 2
  ),
  ARRAY['phase-5', 'maintenance', 'cleanup', 'week-5']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Test Archival Process',
  'Test archival job with sample data. Verify data integrity.',
  'todo',
  'claude',
  53,
  jsonb_build_object(
    'phase', 'Phase 5',
    'week', 5,
    'day', '3',
    'estimated_hours', 1
  ),
  ARRAY['phase-5', 'testing', 'archival', 'week-5']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Create Memory Usage Queries',
  'Write SQL queries for memory analytics: sessions per agent, conversations per day, etc.',
  'todo',
  'claude',
  52,
  jsonb_build_object(
    'phase', 'Phase 5',
    'week', 5,
    'day', '4-5',
    'estimated_hours', 2,
    'deliverable', 'docs/analytics_queries.sql'
  ),
  ARRAY['phase-5', 'analytics', 'sql', 'week-5']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Create Pattern Effectiveness Queries',
  'Queries for pattern analytics: confidence distribution, success rates, usage frequency.',
  'todo',
  'claude',
  51,
  jsonb_build_object(
    'phase', 'Phase 5',
    'week', 5,
    'day', '4-5',
    'estimated_hours', 2
  ),
  ARRAY['phase-5', 'analytics', 'sql', 'week-5']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Document Key Metrics to Monitor',
  'Create monitoring guide with key metrics, thresholds, and alerts.',
  'todo',
  'claude',
  50,
  jsonb_build_object(
    'phase', 'Phase 5',
    'week', 5,
    'day', '4-5',
    'estimated_hours', 2,
    'deliverable', 'docs/monitoring_guide.md'
  ),
  ARRAY['phase-5', 'documentation', 'monitoring', 'week-5']
FROM project;

-- ============================================================================
-- PHASE 6: Integration & Documentation (Week 6)
-- ============================================================================

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Run End-to-End Test Scenarios',
  'Execute all 5 system test scenarios: learning, handoff, parallel, inventory, confidence.',
  'todo',
  'claude',
  49,
  jsonb_build_object(
    'phase', 'Phase 6',
    'week', 6,
    'day', '1-2',
    'estimated_hours', 4
  ),
  ARRAY['phase-6', 'testing', 'e2e', 'week-6']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Test All Collaboration Patterns',
  'Verify handoff, parallel, and review patterns work correctly.',
  'todo',
  'claude',
  48,
  jsonb_build_object(
    'phase', 'Phase 6',
    'week', 6,
    'day', '1-2',
    'estimated_hours', 3
  ),
  ARRAY['phase-6', 'testing', 'collaboration', 'week-6']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Verify Data Consistency',
  'Run data integrity checks across all memory tables.',
  'todo',
  'claude',
  47,
  jsonb_build_object(
    'phase', 'Phase 6',
    'week', 6,
    'day', '1-2',
    'estimated_hours', 2
  ),
  ARRAY['phase-6', 'testing', 'data-integrity', 'week-6']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Test Failure Scenarios and Recovery',
  'Test system behavior under failures: network issues, DB disconnects, etc.',
  'todo',
  'claude',
  46,
  jsonb_build_object(
    'phase', 'Phase 6',
    'week', 6,
    'day', '1-2',
    'estimated_hours', 3
  ),
  ARRAY['phase-6', 'testing', 'failure-recovery', 'week-6']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Write Developer Guide for Memory System',
  'Complete guide on using shared memory system for developers and agents.',
  'todo',
  'claude',
  45,
  jsonb_build_object(
    'phase', 'Phase 6',
    'week', 6,
    'day', '3',
    'estimated_hours', 4,
    'deliverable', 'docs/shared_memory_developer_guide.md'
  ),
  ARRAY['phase-6', 'documentation', 'developer-guide', 'week-6']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Document All MCP Tools with Examples',
  'Complete MCP tools reference with all 20+ new tools documented.',
  'todo',
  'claude',
  44,
  jsonb_build_object(
    'phase', 'Phase 6',
    'week', 6,
    'day', '3',
    'estimated_hours', 4,
    'deliverable', 'docs/mcp_tools_reference.md'
  ),
  ARRAY['phase-6', 'documentation', 'mcp', 'week-6']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Create Architecture Diagrams',
  'Visual diagrams for memory layers, data flow, multi-agent collaboration.',
  'todo',
  'claude',
  43,
  jsonb_build_object(
    'phase', 'Phase 6',
    'week', 6,
    'day', '3',
    'estimated_hours', 3,
    'deliverable', 'docs/architecture_diagrams.md'
  ),
  ARRAY['phase-6', 'documentation', 'architecture', 'week-6']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Write Agent Best Practices Guide',
  'Guidelines for agents on effective memory usage, pattern harvesting, collaboration.',
  'todo',
  'claude',
  42,
  jsonb_build_object(
    'phase', 'Phase 6',
    'week', 6,
    'day', '3',
    'estimated_hours', 3,
    'deliverable', 'docs/agent_best_practices.md'
  ),
  ARRAY['phase-6', 'documentation', 'best-practices', 'week-6']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Run Complete Test Suite',
  'Execute all unit, integration, system, and performance tests.',
  'todo',
  'claude',
  41,
  jsonb_build_object(
    'phase', 'Phase 6',
    'week', 6,
    'day', '4-5',
    'estimated_hours', 3
  ),
  ARRAY['phase-6', 'testing', 'complete', 'week-6']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Fix Remaining Issues',
  'Address any bugs or issues found during final testing.',
  'todo',
  'claude',
  40,
  jsonb_build_object(
    'phase', 'Phase 6',
    'week', 6,
    'day', '4-5',
    'estimated_hours', 4
  ),
  ARRAY['phase-6', 'bug-fixes', 'week-6']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Performance Tuning',
  'Final optimization based on load test results. Target <200ms p95.',
  'todo',
  'claude',
  39,
  jsonb_build_object(
    'phase', 'Phase 6',
    'week', 6,
    'day', '4-5',
    'estimated_hours', 3
  ),
  ARRAY['phase-6', 'performance', 'optimization', 'week-6']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Security Review',
  'Review permissions, API access, SQL injection prevention, authentication.',
  'todo',
  'claude',
  38,
  jsonb_build_object(
    'phase', 'Phase 6',
    'week', 6,
    'day', '4-5',
    'estimated_hours', 3,
    'deliverable', 'docs/security_review_report.md'
  ),
  ARRAY['phase-6', 'security', 'review', 'week-6']
FROM project;

INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, metadata, tags)
SELECT
  project.id,
  'Final Validation Checklist',
  'Run complete validation checklist. Verify 100% test pass rate.',
  'todo',
  'claude',
  37,
  jsonb_build_object(
    'phase', 'Phase 6',
    'week', 6,
    'day', '4-5',
    'estimated_hours', 2,
    'deliverable', 'docs/final_validation_report.md'
  ),
  ARRAY['phase-6', 'validation', 'final', 'week-6']
FROM project;

-- Success!
SELECT 'Shared Memory System project created successfully!' as message;
SELECT COUNT(*) as total_tasks FROM archon_tasks WHERE project_id IN (SELECT id FROM archon_projects WHERE title = 'Shared Memory System Implementation');
