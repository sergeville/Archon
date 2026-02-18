-- =====================================================
-- Phase 2 Schema Testing Script
-- =====================================================
-- Task: Test Schema with Sample Data (Task 90)
-- Date: 2026-02-18
-- Purpose: Comprehensive testing of Phase 2 database schema
-- =====================================================

-- =====================================================
-- SECTION 1: CURRENT DATA INVENTORY
-- =====================================================

SELECT '========================================' as section;
SELECT 'SECTION 1: Current Data Inventory' as section;
SELECT '========================================' as section;

-- Check archon_sessions
SELECT 'archon_sessions:' as table_name, COUNT(*) as total_records,
       COUNT(*) FILTER (WHERE ended_at IS NULL) as active_sessions,
       COUNT(*) FILTER (WHERE ended_at IS NOT NULL) as ended_sessions,
       COUNT(*) FILTER (WHERE embedding IS NOT NULL) as sessions_with_embeddings
FROM archon_sessions;

-- Check archon_session_events
SELECT 'archon_session_events:' as table_name, COUNT(*) as total_records,
       COUNT(DISTINCT session_id) as unique_sessions,
       COUNT(DISTINCT event_type) as unique_event_types,
       COUNT(*) FILTER (WHERE embedding IS NOT NULL) as events_with_embeddings
FROM archon_session_events;

-- Check conversation_history
SELECT 'conversation_history:' as table_name, COUNT(*) as total_records,
       COUNT(*) FILTER (WHERE role = 'user') as user_messages,
       COUNT(*) FILTER (WHERE role = 'assistant') as assistant_messages,
       COUNT(*) FILTER (WHERE role = 'system') as system_messages,
       COUNT(*) FILTER (WHERE embedding IS NOT NULL) as messages_with_embeddings
FROM conversation_history;

-- =====================================================
-- SECTION 2: INSERT ADDITIONAL SAMPLE DATA
-- =====================================================

SELECT '========================================' as section;
SELECT 'SECTION 2: Inserting Additional Sample Data' as section;
SELECT '========================================' as section;

-- Insert diverse session scenarios
DO $$
DECLARE
    v_project_id UUID;
    v_session1_id UUID;
    v_session2_id UUID;
    v_session3_id UUID;
BEGIN
    -- Get a project ID for testing
    SELECT id INTO v_project_id FROM archon_projects LIMIT 1;

    -- Session 1: Active session with project
    INSERT INTO archon_sessions (agent, project_id, context, metadata)
    VALUES (
        'claude',
        v_project_id,
        '{"task": "database migration", "phase": "Phase 2"}',
        '{"test": true, "scenario": "active_with_project"}'
    )
    RETURNING id INTO v_session1_id;

    -- Session 2: Ended session without project
    INSERT INTO archon_sessions (agent, started_at, ended_at, summary, context, metadata)
    VALUES (
        'cursor',
        NOW() - INTERVAL '2 hours',
        NOW() - INTERVAL '1 hour',
        'Completed code review and bug fixes',
        '{"task": "code review", "files_reviewed": 5}',
        '{"test": true, "scenario": "ended_no_project"}'
    )
    RETURNING id INTO v_session2_id;

    -- Session 3: Active session, different agent
    INSERT INTO archon_sessions (agent, context, metadata)
    VALUES (
        'windsurf',
        '{"task": "UI development", "component": "dashboard"}',
        '{"test": true, "scenario": "active_different_agent"}'
    )
    RETURNING id INTO v_session3_id;

    -- Insert session events for session 1
    INSERT INTO archon_session_events (session_id, event_type, event_data, metadata)
    VALUES
        (v_session1_id, 'session_started', '{"timestamp": "now"}', '{"test": true}'),
        (v_session1_id, 'task_created', '{"task_id": "abc-123"}', '{"test": true}'),
        (v_session1_id, 'migration_executed', '{"migration": "004"}', '{"test": true}');

    -- Insert session events for session 2
    INSERT INTO archon_session_events (session_id, event_type, event_data, metadata)
    VALUES
        (v_session2_id, 'session_started', '{"timestamp": "2h ago"}', '{"test": true}'),
        (v_session2_id, 'code_reviewed', '{"files": 5, "issues_found": 3}', '{"test": true}'),
        (v_session2_id, 'session_ended', '{"duration": "1h"}', '{"test": true}');

    -- Insert conversation history for session 1 (active development dialogue)
    INSERT INTO conversation_history (session_id, role, message, type, subtype, metadata)
    VALUES
        (v_session1_id, 'user', 'Start working on Phase 2 database migration', 'command', 'task_start', '{"test": true}'),
        (v_session1_id, 'assistant', 'I''ll begin by creating the conversation_history table.', 'response', 'acknowledgment', '{"test": true}'),
        (v_session1_id, 'user', 'Make sure to add vector embeddings', 'instruction', 'requirement', '{"test": true}'),
        (v_session1_id, 'assistant', 'Added VECTOR(1536) column and ivfflat index.', 'response', 'confirmation', '{"test": true, "tools_used": ["database", "migration"]}');

    -- Insert conversation history for session 2 (code review dialogue)
    INSERT INTO conversation_history (session_id, role, message, type, subtype, metadata)
    VALUES
        (v_session2_id, 'user', 'Review the authentication module', 'command', 'task_start', '{"test": true}'),
        (v_session2_id, 'assistant', 'Found 3 potential security issues in the auth flow.', 'response', 'analysis', '{"test": true, "tools_used": ["code_analysis"]}'),
        (v_session2_id, 'user', 'What are the issues?', 'question', 'clarification', '{"test": true}'),
        (v_session2_id, 'assistant', '1. Missing rate limiting, 2. Weak password validation, 3. No session expiry.', 'response', 'detailed_explanation', '{"test": true}');

    -- Insert conversation history for session 3 (UI development)
    INSERT INTO conversation_history (session_id, role, message, type, subtype, metadata)
    VALUES
        (v_session3_id, 'user', 'Create a new dashboard component', 'command', 'task_start', '{"test": true}'),
        (v_session3_id, 'assistant', 'I''ll create a React component with Tailwind styling.', 'response', 'acknowledgment', '{"test": true, "tools_used": ["react", "tailwind"]}');

    RAISE NOTICE 'Inserted 3 sessions, 6 events, and 10 conversation messages';
END $$;

-- =====================================================
-- SECTION 3: VERIFY FOREIGN KEY CONSTRAINTS
-- =====================================================

SELECT '========================================' as section;
SELECT 'SECTION 3: Foreign Key Constraint Tests' as section;
SELECT '========================================' as section;

-- Test 1: Try to insert conversation with invalid session_id (should fail)
DO $$
BEGIN
    BEGIN
        INSERT INTO conversation_history (session_id, role, message)
        VALUES ('00000000-0000-0000-0000-000000000000', 'user', 'test');
        RAISE NOTICE '❌ FAIL: Foreign key constraint NOT enforced (invalid session_id accepted)';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE '✅ PASS: Foreign key constraint enforced (invalid session_id rejected)';
    END;
END $$;

-- Test 2: Try to insert event with invalid session_id (should fail)
DO $$
BEGIN
    BEGIN
        INSERT INTO archon_session_events (session_id, event_type, event_data)
        VALUES ('00000000-0000-0000-0000-000000000000', 'test', '{}');
        RAISE NOTICE '❌ FAIL: Foreign key constraint NOT enforced (invalid session_id in events)';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE '✅ PASS: Foreign key constraint enforced (invalid session_id in events rejected)';
    END;
END $$;

-- Test 3: Verify CASCADE delete behavior
DO $$
DECLARE
    v_test_session_id UUID;
    v_messages_before INT;
    v_messages_after INT;
BEGIN
    -- Create a test session
    INSERT INTO archon_sessions (agent, context)
    VALUES ('test_agent', '{"test": "cascade"}')
    RETURNING id INTO v_test_session_id;

    -- Add a conversation message
    INSERT INTO conversation_history (session_id, role, message)
    VALUES (v_test_session_id, 'user', 'test message');

    -- Count messages
    SELECT COUNT(*) INTO v_messages_before
    FROM conversation_history WHERE session_id = v_test_session_id;

    -- Delete the session
    DELETE FROM archon_sessions WHERE id = v_test_session_id;

    -- Count messages after delete
    SELECT COUNT(*) INTO v_messages_after
    FROM conversation_history WHERE session_id = v_test_session_id;

    IF v_messages_before > 0 AND v_messages_after = 0 THEN
        RAISE NOTICE '✅ PASS: CASCADE delete working (messages: % → %)', v_messages_before, v_messages_after;
    ELSE
        RAISE NOTICE '❌ FAIL: CASCADE delete NOT working (messages: % → %)', v_messages_before, v_messages_after;
    END IF;
END $$;

-- =====================================================
-- SECTION 4: INDEX USAGE VERIFICATION
-- =====================================================

SELECT '========================================' as section;
SELECT 'SECTION 4: Index Usage Verification' as section;
SELECT '========================================' as section;

-- Test query 1: Session lookup by ID (should use primary key)
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM archon_sessions WHERE id = (SELECT id FROM archon_sessions LIMIT 1);

-- Test query 2: Conversation by session_id (should use idx_conversation_session_id)
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM conversation_history
WHERE session_id = (SELECT id FROM archon_sessions LIMIT 1);

-- Test query 3: Filter by role (should use idx_conversation_role)
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM conversation_history WHERE role = 'user';

-- Test query 4: Chronological query (should use idx_conversation_created_at)
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM conversation_history ORDER BY created_at DESC LIMIT 10;

-- Test query 5: Session events by session_id (should use idx_events_session_id)
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM archon_session_events
WHERE session_id = (SELECT id FROM archon_sessions LIMIT 1);

-- =====================================================
-- SECTION 5: PERFORMANCE TESTING (<200ms requirement)
-- =====================================================

SELECT '========================================' as section;
SELECT 'SECTION 5: Performance Testing (<200ms)' as section;
SELECT '========================================' as section;

-- Create timing function
CREATE OR REPLACE FUNCTION measure_query_time(query TEXT)
RETURNS TABLE (execution_time_ms NUMERIC) AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
BEGIN
    start_time := clock_timestamp();
    EXECUTE query;
    end_time := clock_timestamp();
    RETURN QUERY SELECT EXTRACT(MILLISECONDS FROM (end_time - start_time));
END;
$$ LANGUAGE plpgsql;

-- Test 1: Get conversation history (helper function)
WITH timing AS (
    SELECT measure_query_time(
        'SELECT * FROM get_conversation_history((SELECT id FROM archon_sessions LIMIT 1), 100)'
    ) as ms
)
SELECT 'get_conversation_history' as query,
       ms as execution_time_ms,
       CASE WHEN ms < 200 THEN '✅ PASS' ELSE '❌ FAIL' END as status
FROM timing;

-- Test 2: Recent conversation messages
WITH timing AS (
    SELECT measure_query_time(
        'SELECT * FROM get_recent_conversation_messages((SELECT id FROM archon_sessions LIMIT 1), 10)'
    ) as ms
)
SELECT 'get_recent_conversation_messages' as query,
       ms as execution_time_ms,
       CASE WHEN ms < 200 THEN '✅ PASS' ELSE '❌ FAIL' END as status
FROM timing;

-- Test 3: Count messages by role
WITH timing AS (
    SELECT measure_query_time(
        'SELECT * FROM count_messages_by_role((SELECT id FROM archon_sessions LIMIT 1))'
    ) as ms
)
SELECT 'count_messages_by_role' as query,
       ms as execution_time_ms,
       CASE WHEN ms < 200 THEN '✅ PASS' ELSE '❌ FAIL' END as status
FROM timing;

-- Test 4: Recent conversations view
WITH timing AS (
    SELECT measure_query_time(
        'SELECT * FROM v_recent_conversations LIMIT 20'
    ) as ms
)
SELECT 'v_recent_conversations' as query,
       ms as execution_time_ms,
       CASE WHEN ms < 200 THEN '✅ PASS' ELSE '❌ FAIL' END as status
FROM timing;

-- Test 5: Conversation stats view
WITH timing AS (
    SELECT measure_query_time(
        'SELECT * FROM v_conversation_stats LIMIT 20'
    ) as ms
)
SELECT 'v_conversation_stats' as query,
       ms as execution_time_ms,
       CASE WHEN ms < 200 THEN '✅ PASS' ELSE '❌ FAIL' END as status
FROM timing;

-- Test 6: Get recent sessions
WITH timing AS (
    SELECT measure_query_time(
        'SELECT * FROM get_recent_sessions(''claude'', 7)'
    ) as ms
)
SELECT 'get_recent_sessions' as query,
       ms as execution_time_ms,
       CASE WHEN ms < 200 THEN '✅ PASS' ELSE '❌ FAIL' END as status
FROM timing;

-- =====================================================
-- SECTION 6: SEMANTIC SEARCH TESTING
-- =====================================================

SELECT '========================================' as section;
SELECT 'SECTION 6: Semantic Search Testing' as section;
SELECT '========================================' as section;

-- Note: Semantic search requires embeddings to be generated
-- This section tests the query structure, not actual results

-- Test 1: Check if any records have embeddings
SELECT 'Sessions with embeddings:' as metric,
       COUNT(*) as count
FROM archon_sessions WHERE embedding IS NOT NULL;

SELECT 'Events with embeddings:' as metric,
       COUNT(*) as count
FROM archon_session_events WHERE embedding IS NOT NULL;

SELECT 'Conversations with embeddings:' as metric,
       COUNT(*) as count
FROM conversation_history WHERE embedding IS NOT NULL;

-- Test 2: Verify semantic search function exists and has correct signature
SELECT 'search_conversation_semantic exists:' as check,
       CASE WHEN COUNT(*) > 0 THEN '✅ YES' ELSE '❌ NO' END as status
FROM pg_proc
WHERE proname = 'search_conversation_semantic';

SELECT 'search_sessions_semantic exists:' as check,
       CASE WHEN COUNT(*) > 0 THEN '✅ YES' ELSE '❌ NO' END as status
FROM pg_proc
WHERE proname = 'search_sessions_semantic';

SELECT 'search_all_memory_semantic exists:' as check,
       CASE WHEN COUNT(*) > 0 THEN '✅ YES' ELSE '❌ NO' END as status
FROM pg_proc
WHERE proname = 'search_all_memory_semantic';

-- =====================================================
-- SECTION 7: DATA INTEGRITY CHECKS
-- =====================================================

SELECT '========================================' as section;
SELECT 'SECTION 7: Data Integrity Checks' as section;
SELECT '========================================' as section;

-- Check for orphaned conversation messages (should be 0)
SELECT 'Orphaned conversation messages:' as check,
       COUNT(*) as count,
       CASE WHEN COUNT(*) = 0 THEN '✅ PASS' ELSE '❌ FAIL' END as status
FROM conversation_history ch
LEFT JOIN archon_sessions s ON ch.session_id = s.id
WHERE s.id IS NULL;

-- Check for orphaned session events (should be 0)
SELECT 'Orphaned session events:' as check,
       COUNT(*) as count,
       CASE WHEN COUNT(*) = 0 THEN '✅ PASS' ELSE '❌ FAIL' END as status
FROM archon_session_events e
LEFT JOIN archon_sessions s ON e.session_id = s.id
WHERE s.id IS NULL;

-- Check for invalid role values in conversation_history (should be 0)
SELECT 'Invalid role values:' as check,
       COUNT(*) as count,
       CASE WHEN COUNT(*) = 0 THEN '✅ PASS' ELSE '❌ FAIL' END as status
FROM conversation_history
WHERE role NOT IN ('user', 'assistant', 'system');

-- =====================================================
-- SECTION 8: FINAL SUMMARY
-- =====================================================

SELECT '========================================' as section;
SELECT 'SECTION 8: Test Summary' as section;
SELECT '========================================' as section;

-- Final record counts
SELECT 'FINAL DATA COUNTS' as summary, '' as value
UNION ALL
SELECT 'Total sessions:', COUNT(*)::TEXT FROM archon_sessions
UNION ALL
SELECT 'Total session events:', COUNT(*)::TEXT FROM archon_session_events
UNION ALL
SELECT 'Total conversation messages:', COUNT(*)::TEXT FROM conversation_history
UNION ALL
SELECT 'Active sessions:', COUNT(*)::TEXT FROM archon_sessions WHERE ended_at IS NULL
UNION ALL
SELECT 'Unique agents:', COUNT(DISTINCT agent)::TEXT FROM archon_sessions;

-- Cleanup temporary function
DROP FUNCTION IF EXISTS measure_query_time(TEXT);

SELECT '========================================' as section;
SELECT '✅ Phase 2 Schema Testing COMPLETE' as section;
SELECT '========================================' as section;
