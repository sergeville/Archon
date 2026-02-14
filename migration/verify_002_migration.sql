-- =====================================================
-- Verification Script for Migration 002
-- =====================================================
-- Run this in Supabase SQL Editor AFTER running 002_session_memory.sql
-- to verify everything was created correctly
-- =====================================================

-- =====================================================
-- 1. CHECK TABLES CREATED
-- =====================================================

-- Should return 2 rows (archon_sessions, archon_session_events)
SELECT
    table_name,
    table_type
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('archon_sessions', 'archon_session_events')
ORDER BY table_name;

-- Expected: 2 tables found

-- =====================================================
-- 2. CHECK COLUMNS ADDED
-- =====================================================

-- Check embedding column on archon_tasks
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'archon_tasks'
  AND column_name = 'embedding';

-- Expected: 1 row (tasks.embedding)

-- Check embedding column on archon_projects
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'archon_projects'
  AND column_name = 'embedding';

-- Expected: 1 row (projects.embedding)

-- =====================================================
-- 3. CHECK INDEXES CREATED
-- =====================================================

-- Should return ~8 indexes
SELECT
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND (
    tablename IN ('archon_sessions', 'archon_session_events')
    OR indexname LIKE '%embedding%'
  )
ORDER BY tablename, indexname;

-- Expected: Multiple indexes including embedding indexes

-- =====================================================
-- 4. CHECK FUNCTIONS CREATED
-- =====================================================

-- Should return 4 functions
SELECT
    routine_name,
    routine_type
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_name IN (
    'get_recent_sessions',
    'search_sessions_semantic',
    'get_last_session',
    'count_sessions_by_agent'
  )
ORDER BY routine_name;

-- Expected: 4 functions

-- =====================================================
-- 5. CHECK VIEWS CREATED
-- =====================================================

-- Should return 2 views
SELECT
    table_name,
    table_type
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'VIEW'
  AND table_name IN ('v_recent_sessions', 'v_active_sessions')
ORDER BY table_name;

-- Expected: 2 views

-- =====================================================
-- 6. TEST DATA INSERTION
-- =====================================================

-- Test inserting a session
INSERT INTO archon_sessions (agent, summary)
VALUES ('test', 'Migration verification test session')
RETURNING id, agent, started_at;

-- Expected: 1 row inserted, returns UUID

-- Get the session we just created
SELECT * FROM archon_sessions WHERE agent = 'test';

-- Expected: 1 row with our test session

-- Test inserting an event
INSERT INTO archon_session_events (
    session_id,
    event_type,
    event_data
)
SELECT
    id,
    'test_event',
    '{"action": "verification", "status": "success"}'::jsonb
FROM archon_sessions
WHERE agent = 'test'
RETURNING id, event_type, timestamp;

-- Expected: 1 row inserted

-- =====================================================
-- 7. TEST HELPER FUNCTIONS
-- =====================================================

-- Test get_recent_sessions
SELECT * FROM get_recent_sessions('test', 7, 10);

-- Expected: 1 row with our test session

-- Test get_last_session
SELECT * FROM get_last_session('test');

-- Expected: 1 row with our test session

-- Test count_sessions_by_agent
SELECT count_sessions_by_agent('test', 30);

-- Expected: Returns 1

-- =====================================================
-- 8. TEST VIEWS
-- =====================================================

-- Test v_recent_sessions view
SELECT * FROM v_recent_sessions WHERE agent = 'test';

-- Expected: 1 row with our test session

-- Test v_active_sessions view (our test session should appear)
SELECT * FROM v_active_sessions WHERE agent = 'test';

-- Expected: 1 row (test session not ended)

-- =====================================================
-- 9. CLEANUP TEST DATA
-- =====================================================

-- Delete test session (cascade will delete events too)
DELETE FROM archon_sessions WHERE agent = 'test';

-- Verify cleanup
SELECT COUNT(*) FROM archon_sessions WHERE agent = 'test';

-- Expected: 0

SELECT COUNT(*) FROM archon_session_events
WHERE session_id IN (
    SELECT id FROM archon_sessions WHERE agent = 'test'
);

-- Expected: 0

-- =====================================================
-- 10. FINAL VERIFICATION SUMMARY
-- =====================================================

-- Run this to get a complete summary
SELECT
    'Tables' as category,
    COUNT(*) as count
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('archon_sessions', 'archon_session_events')

UNION ALL

SELECT
    'Embedding Columns' as category,
    COUNT(*) as count
FROM information_schema.columns
WHERE table_schema = 'public'
  AND column_name = 'embedding'
  AND table_name IN ('archon_tasks', 'archon_projects')

UNION ALL

SELECT
    'Indexes' as category,
    COUNT(*) as count
FROM pg_indexes
WHERE schemaname = 'public'
  AND (
    tablename IN ('archon_sessions', 'archon_session_events')
    OR indexname LIKE '%embedding%'
  )

UNION ALL

SELECT
    'Functions' as category,
    COUNT(*) as count
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_name IN (
    'get_recent_sessions',
    'search_sessions_semantic',
    'get_last_session',
    'count_sessions_by_agent'
  )

UNION ALL

SELECT
    'Views' as category,
    COUNT(*) as count
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'VIEW'
  AND table_name IN ('v_recent_sessions', 'v_active_sessions');

-- Expected results:
-- Tables: 2
-- Embedding Columns: 2
-- Indexes: ~8
-- Functions: 4
-- Views: 2

-- =====================================================
-- ✅ VERIFICATION COMPLETE
-- =====================================================
-- If all checks pass, migration was successful!
-- You can now proceed to Day 2: SessionService implementation
-- =====================================================
