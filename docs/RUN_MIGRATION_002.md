# How to Run Migration 002: Session Memory

**Date:** 2026-02-14
**Migration:** 002_session_memory.sql
**Purpose:** Add session tracking and semantic search capabilities
**Estimated Time:** 5-10 minutes

---

## Prerequisites ✅

Before running this migration, verify:

- [x] Archon services are running (`docker compose ps`)
- [x] You have access to Supabase dashboard
- [x] Migration file exists: `migration/002_session_memory.sql`
- [x] pgvector extension is enabled (should be from base setup)

---

## Option 1: Supabase Dashboard (Recommended)

### Step 1: Open the Migration File

```bash
# Read the migration file
cat ~/Documents/Projects/Archon/migration/002_session_memory.sql
```

### Step 2: Open Supabase Dashboard

```bash
# Open Supabase in browser
open "https://supabase.com/dashboard"
```

Or manually navigate to: https://supabase.com/dashboard

### Step 3: Navigate to SQL Editor

1. Select your Archon project
2. Click "SQL Editor" in left sidebar
3. Click "New Query"

### Step 4: Paste and Execute

1. **Copy the entire contents** of `002_session_memory.sql`
2. **Paste** into the SQL Editor
3. **Click "Run"** (or press Cmd+Enter / Ctrl+Enter)
4. **Wait** for execution (should take 5-10 seconds)

### Step 5: Check for Errors

**Success:**
```
Success. No rows returned.
```
or
```
CREATE TABLE
CREATE INDEX
...
INSERT 0 1
```

**If you see errors:**
- Most common: pgvector not enabled → Run `CREATE EXTENSION vector;` first
- Table already exists → Safe to ignore if `IF NOT EXISTS` was used
- Permission denied → Check you're using service role key

### Step 6: Run Verification

1. Create a **new query** in SQL Editor
2. **Copy contents** of `verify_002_migration.sql`
3. **Paste** and **Run**
4. **Review results** - all checks should pass

**Expected Summary:**
```
category              | count
----------------------|-------
Tables                | 2
Embedding Columns     | 2
Indexes               | 8
Functions             | 4
Views                 | 2
```

---

## Option 2: Command Line (If You Have psql Access)

### Step 1: Get Database URL

You need the PostgreSQL connection string (not the HTTP URL).

**In Supabase Dashboard:**
1. Go to Project Settings → Database
2. Find "Connection String" section
3. Select "URI" tab
4. Copy the connection string (starts with `postgresql://`)

### Step 2: Add to Environment

```bash
# Add to .env file (temporary)
echo 'DATABASE_URL="postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres"' >> .env

# Or export directly
export DATABASE_URL="postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres"
```

### Step 3: Run Migration

```bash
# Navigate to Archon directory
cd ~/Documents/Projects/Archon

# Run migration
psql "$DATABASE_URL" -f migration/002_session_memory.sql

# Run verification
psql "$DATABASE_URL" -f migration/verify_002_migration.sql
```

**Expected Output:**
```
CREATE TABLE
CREATE INDEX
CREATE FUNCTION
...
INSERT 0 1
```

---

## Verification Checklist

After running the migration, verify these items:

### Tables Created
- [ ] `archon_sessions` table exists
- [ ] `archon_session_events` table exists

### Columns Added
- [ ] `archon_tasks.embedding` column exists (VECTOR(1536))
- [ ] `archon_projects.embedding` column exists (VECTOR(1536))

### Indexes Created
- [ ] `idx_sessions_agent`
- [ ] `idx_sessions_project`
- [ ] `idx_sessions_started`
- [ ] `idx_sessions_embedding`
- [ ] `idx_events_session`
- [ ] `idx_events_type`
- [ ] `idx_events_timestamp`
- [ ] `idx_events_embedding`
- [ ] `idx_tasks_embedding`
- [ ] `idx_projects_embedding`

### Functions Created
- [ ] `get_recent_sessions()`
- [ ] `search_sessions_semantic()`
- [ ] `get_last_session()`
- [ ] `count_sessions_by_agent()`

### Views Created
- [ ] `v_recent_sessions`
- [ ] `v_active_sessions`

### Test Queries Work
- [ ] Can insert test session
- [ ] Can query sessions
- [ ] Helper functions return results
- [ ] Views return data

---

## Quick Verification Commands

Run these in Supabase SQL Editor to verify:

### Check Tables
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name LIKE 'archon_session%';
```

**Expected:** 2 rows

### Check Columns
```sql
SELECT table_name, column_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND column_name = 'embedding'
  AND table_name IN ('archon_tasks', 'archon_projects');
```

**Expected:** 2 rows

### Test Insert
```sql
INSERT INTO archon_sessions (agent, summary)
VALUES ('test', 'Verification test')
RETURNING id, agent, started_at;
```

**Expected:** 1 row with UUID

### Cleanup Test
```sql
DELETE FROM archon_sessions WHERE agent = 'test';
```

---

## Troubleshooting

### Error: "extension vector does not exist"

**Solution:**
```sql
-- Run this first
CREATE EXTENSION IF NOT EXISTS vector;

-- Then run the migration
```

### Error: "relation archon_projects does not exist"

**Problem:** Base schema not installed

**Solution:**
```sql
-- Run base setup first
-- Use migration/complete_setup.sql
```

### Error: "column embedding already exists"

**Status:** ✅ Safe to ignore

This means the column was already added (migration ran before or partially).

### Error: "permission denied"

**Problem:** Using wrong role

**Solution:**
- Make sure you're using the service role key
- Check RLS policies in Supabase dashboard

### Warning: "ivfflat index may be slow"

**Status:** ✅ Safe to ignore

IVFFlat indexes are created with placeholder size. They'll optimize as data grows.

---

## What This Migration Does

### New Capabilities

After this migration, Archon can:

✅ **Track agent sessions**
- Create/end sessions
- Log events within sessions
- Associate sessions with projects

✅ **Generate session summaries**
- AI-generated summaries (in Day 5)
- Metadata storage (key events, decisions, outcomes)

✅ **Search semantically**
- Find similar sessions
- Search tasks by meaning
- Search projects by concept

✅ **Query temporally**
- "What happened in last 7 days?"
- "Get my last session"
- "Recent sessions for claude"

### Database Changes

**New Tables:** 2
- `archon_sessions` (11 columns)
- `archon_session_events` (7 columns)

**Modified Tables:** 2
- `archon_tasks` (+1 column: embedding)
- `archon_projects` (+1 column: embedding)

**New Indexes:** 10 (8 new tables + 2 on existing)

**New Functions:** 4 helper functions

**New Views:** 2 convenience views

**Total Size:** ~100 KB (empty tables)

---

## After Migration Success

### Next Steps (Day 2)

1. **Implement SessionService**
   - File: `python/src/server/services/session_service.py`
   - CRUD operations for sessions
   - Event logging
   - Embedding generation

2. **Create API Endpoints (Day 3)**
   - REST API for sessions
   - MCP tools for session management

3. **Build Frontend (Day 6-7)**
   - Session list view
   - Session detail view
   - Memory search

### Update Project Tasks

Mark Day 1 complete in Archon:

```bash
# Create a new task for Day 1 completion
curl -X POST "http://localhost:8181/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "b231255f-6ed9-4440-80de-958bcf7b4f9f",
    "title": "Day 1: Create Session Memory Database Schema",
    "description": "Created archon_sessions and archon_session_events tables, added embedding columns to existing tables, created indexes and helper functions.",
    "status": "done",
    "assignee": "claude",
    "priority": "high",
    "feature": "Phase 2: Session Memory & Semantic Search"
  }'
```

---

## Success Indicators

You'll know the migration succeeded if:

- ✅ No errors in SQL Editor
- ✅ All verification queries return expected counts
- ✅ Can insert and query test sessions
- ✅ Helper functions work correctly
- ✅ Views return data

**If ALL checks pass:** Migration successful! ✅

**Progress:** 75% → ~77% (+2% - database layer complete)

---

## Need Help?

### Common Issues

**Issue:** Supabase connection timeout
**Solution:** Check your internet connection, try again

**Issue:** Can't find SQL Editor
**Solution:** Make sure you're in the correct Supabase project

**Issue:** Migration seems stuck
**Solution:** Refresh page, check Supabase status

### Support

If you encounter issues:

1. Check the verification script output
2. Review error messages carefully
3. Check Supabase dashboard logs
4. Try running migration in smaller chunks

---

## Rollback (If Needed)

If you need to undo this migration:

```sql
-- WARNING: This will delete all session data!

-- Drop tables (cascade will drop related objects)
DROP TABLE IF EXISTS archon_session_events CASCADE;
DROP TABLE IF EXISTS archon_sessions CASCADE;

-- Remove embedding columns
ALTER TABLE archon_tasks DROP COLUMN IF EXISTS embedding;
ALTER TABLE archon_projects DROP COLUMN IF EXISTS embedding;

-- Drop functions
DROP FUNCTION IF EXISTS get_recent_sessions;
DROP FUNCTION IF EXISTS search_sessions_semantic;
DROP FUNCTION IF EXISTS get_last_session;
DROP FUNCTION IF EXISTS count_sessions_by_agent;

-- Drop views
DROP VIEW IF EXISTS v_recent_sessions;
DROP VIEW IF EXISTS v_active_sessions;

-- Remove from migrations table
DELETE FROM archon_migrations WHERE version = '002';
```

---

## Summary

**Migration:** 002_session_memory.sql
**Status:** Ready to run
**Method:** Supabase Dashboard (recommended) or psql
**Time:** 5-10 minutes
**Risk:** Low (uses IF NOT EXISTS, safe to re-run)
**Verification:** verify_002_migration.sql
**Next:** Day 2 - SessionService implementation

**You are ready to run this migration!** 🚀

---

**Created By:** Claude (Archon Agent)
**Date:** 2026-02-14
**Project:** Shared Memory System Implementation
**Phase:** Phase 2, Day 1
