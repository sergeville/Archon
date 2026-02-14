# Database Verification Tests - Session Memory Migration

**Date:** 2026-02-14
**Purpose:** Comprehensive verification of 002_session_memory migration
**Status:** Run these queries in Supabase SQL Editor

---

## Test 1: Check pgvector Extension

```sql
SELECT
    'pgvector_extension' as check_name,
    CASE
        WHEN COUNT(*) > 0 THEN '✅ PASS'
        ELSE '❌ FAIL - pgvector not enabled'
    END as status,
    extversion as version
FROM pg_extension
WHERE extname = 'vector';
```

**Expected:** 1 row with ✅ PASS

---

## Test 2: Check Tables Created

```sql
SELECT
    table_name,
    CASE
        WHEN COUNT(*) > 0 THEN '✅ EXISTS'
        ELSE '❌ MISSING'
    END as status
FROM (
    SELECT 'archon_sessions' as table_name
    UNION ALL
    SELECT 'archon_session_events'
) t
LEFT JOIN information_schema.tables ist ON
    ist.table_schema = 'public' AND
    ist.table_name = t.table_name
GROUP BY t.table_name
ORDER BY t.table_name;
```

**Expected:** 2 rows, both ✅ EXISTS

---

## Test 3: Check Embedding Columns Added

```sql
SELECT
    table_name,
    column_name,
    data_type,
    CASE
        WHEN data_type = 'USER-DEFINED' THEN '✅ VECTOR TYPE'
        ELSE '❌ WRONG TYPE'
    END as status
FROM information_schema.columns
WHERE table_name IN ('archon_tasks', 'archon_projects')
  AND column_name = 'embedding'
ORDER BY table_name;
```

**Expected:** 2 rows, both ✅ VECTOR TYPE

---

## Test 4: Check Indexes Created

```sql
SELECT
    schemaname,
    tablename,
    indexname,
    '✅ EXISTS' as status
FROM pg_indexes
WHERE schemaname = 'public'
  AND (
    indexname LIKE 'idx_sessions_%' OR
    indexname LIKE 'idx_events_%' OR
    indexname LIKE 'idx_tasks_embedding' OR
    indexname LIKE 'idx_projects_embedding'
  )
ORDER BY tablename, indexname;
```

**Expected:** 8-10 indexes

**Critical indexes:**
- idx_sessions_agent
- idx_sessions_project
- idx_sessions_started
- idx_sessions_embedding (ivfflat)
- idx_events_session
- idx_events_type
- idx_events_timestamp
- idx_events_embedding (ivfflat)
- idx_tasks_embedding (ivfflat)
- idx_projects_embedding (ivfflat)

---

## Test 5: Check Helper Functions

```sql
SELECT
    routine_name,
    routine_type,
    '✅ EXISTS' as status
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_name IN (
    'get_recent_sessions',
    'get_last_session',
    'search_sessions_semantic',
    'count_sessions_by_agent'
  )
ORDER BY routine_name;
```

**Expected:** 2-4 functions (depends on which version was run)

---

## Test 6: Check RLS Policies

```sql
SELECT
    tablename,
    policyname,
    '✅ EXISTS' as status
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename IN ('archon_sessions', 'archon_session_events')
ORDER BY tablename, policyname;
```

**Expected:** 4 policies (2 per table)

---

## Test 7: Test Data Insertion

```sql
-- Insert a test session
INSERT INTO archon_sessions (agent, summary, metadata)
VALUES (
    'test-agent',
    'This is a test session to verify database functionality',
    jsonb_build_object(
        'test', true,
        'created_by', 'verification_script'
    )
)
RETURNING
    id,
    agent,
    '✅ INSERT SUCCESS' as status;
```

**Expected:** 1 row returned with test session ID

---

## Test 8: Test Event Insertion

```sql
-- Insert a test event (use the session ID from Test 7)
WITH test_session AS (
    SELECT id FROM archon_sessions WHERE agent = 'test-agent' LIMIT 1
)
INSERT INTO archon_session_events (session_id, event_type, event_data)
SELECT
    id,
    'test_event',
    jsonb_build_object('message', 'Test event verification')
FROM test_session
RETURNING
    id,
    event_type,
    '✅ EVENT INSERT SUCCESS' as status;
```

**Expected:** 1 row returned with event ID

---

## Test 9: Test Helper Function

```sql
-- Test get_last_session function
SELECT
    id,
    agent,
    summary,
    '✅ FUNCTION WORKS' as status
FROM get_last_session('test-agent');
```

**Expected:** 1 row with the test session

---

## Test 10: Clean Up Test Data

```sql
-- Delete test data
DELETE FROM archon_sessions WHERE agent = 'test-agent'
RETURNING agent, '✅ CLEANUP COMPLETE' as status;
```

**Expected:** 1 row deleted

---

## Test 11: Verify Embedding Column Structure

```sql
SELECT
    c.table_name,
    c.column_name,
    c.data_type,
    c.udt_name,
    CASE
        WHEN c.udt_name = 'vector' THEN '✅ CORRECT TYPE'
        ELSE '❌ WRONG TYPE'
    END as status,
    format_type(a.atttypid, a.atttypmod) as full_type
FROM information_schema.columns c
JOIN pg_attribute a ON
    a.attname = c.column_name AND
    a.attrelid = (c.table_schema || '.' || c.table_name)::regclass
WHERE c.table_name IN ('archon_sessions', 'archon_session_events', 'archon_tasks', 'archon_projects')
  AND c.column_name = 'embedding'
ORDER BY c.table_name;
```

**Expected:** 4 rows showing `vector(1536)` type

---

## Complete Status Summary

```sql
-- Run this to get overall migration status
SELECT
    'Migration Status' as check_category,
    json_build_object(
        'pgvector_enabled', EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector'),
        'sessions_table', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'archon_sessions'),
        'events_table', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'archon_session_events'),
        'tasks_embedding', EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name = 'archon_tasks' AND column_name = 'embedding'),
        'projects_embedding', EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name = 'archon_projects' AND column_name = 'embedding'),
        'indexes_count', (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public' AND (indexname LIKE 'idx_sessions_%' OR indexname LIKE 'idx_events_%' OR indexname = 'idx_tasks_embedding' OR indexname = 'idx_projects_embedding')),
        'functions_count', (SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema = 'public' AND routine_name IN ('get_recent_sessions', 'get_last_session')),
        'policies_count', (SELECT COUNT(*) FROM pg_policies WHERE schemaname = 'public' AND tablename IN ('archon_sessions', 'archon_session_events'))
    ) as status;
```

**Expected:** All boolean values = `true`, counts > 0

---

## Success Criteria

✅ **Migration is successful if:**
1. pgvector extension exists
2. Both tables (archon_sessions, archon_session_events) exist
3. Embedding columns exist on tasks and projects (type: vector(1536))
4. At least 8 indexes created
5. At least 2 helper functions exist
6. 4 RLS policies exist
7. Can insert test data successfully
8. Functions return data correctly

---

## If Tests Fail

**pgvector not enabled:**
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

**Tables missing:**
- Re-run the migration SQL with pgvector enabled first

**Indexes missing:**
- Indexes may fail if pgvector wasn't enabled first
- Re-run migration after enabling pgvector

**Functions missing:**
- Check for SQL errors in migration execution
- Functions may have been skipped due to earlier errors

---

## Next Steps After Verification

1. ✅ Mark migration task as complete in Archon
2. 📝 Update task status: Day 1 complete
3. 🚀 Proceed to Day 2: Implement SessionService
4. 📊 Document any issues or deviations from expected results

---

**Last Updated:** 2026-02-14
**Migration File:** `migration/002_session_memory.sql`
**Project:** Shared Memory System Implementation (ID: b231255f-6ed9-4440-80de-958bcf7b4f9f)
