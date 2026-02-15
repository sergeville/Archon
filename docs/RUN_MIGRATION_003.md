# How to Run Migration 003: Unified Memory Search

**Date:** 2026-02-14
**Migration:** 003_unified_memory_search.sql
**Purpose:** Add database function for unified semantic search across all memory layers
**Estimated Time:** 2 minutes

---

## Prerequisites ✅

Before running this migration, verify:

- [x] Migration 002 is complete (session tables and embedding columns exist)
- [x] Archon services are running (`docker compose ps`)
- [x] You have access to Supabase dashboard
- [x] Migration file exists: `migration/003_unified_memory_search.sql`

---

## Option 1: Supabase Dashboard (Recommended)

### Step 1: Open the Migration File

```bash
# Read the migration file
cat /Users/sergevilleneuve/Documents/Projects/Archon/migration/003_unified_memory_search.sql
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

1. **Copy the entire contents** of `003_unified_memory_search.sql`
2. **Paste** into the SQL Editor
3. **Click "Run"** (or press Cmd+Enter / Ctrl+Enter)
4. **Wait** for execution (should take 2-3 seconds)

### Step 5: Check for Success

**Success:**
```
Success. No rows returned.
```
or
```
CREATE FUNCTION
INSERT 0 1
NOTICE: Migration 003: COMPLETE
```

**If you see errors:**
- Most common: Migration 002 not run → Run `002_session_memory.sql` first
- Function exists → Safe (idempotent migration)
- Permission denied → Check you're using service role key

---

## Option 2: Command Line (If You Have psql Access)

### Step 1: Run Migration

```bash
# Navigate to Archon directory
cd /Users/sergevilleneuve/Documents/Projects/Archon

# Run migration
psql "$DATABASE_URL" -f migration/003_unified_memory_search.sql
```

**Expected Output:**
```
CREATE FUNCTION
INSERT 0 1
NOTICE: Migration 003: COMPLETE
```

---

## Verification

After running the migration, verify the function exists:

### Check Function Exists

```sql
SELECT proname, prokind
FROM pg_proc
WHERE proname = 'search_all_memory_semantic';
```

**Expected:** 1 row (function)

### Check Migration Record

```sql
SELECT version, name, applied_at
FROM archon_migrations
WHERE version = '003';
```

**Expected:** 1 row with current timestamp

---

## What This Migration Does

### New Capabilities

After this migration, Archon can:

✅ **Search all memory layers semantically**
- Unified search across sessions, tasks, and projects
- Single endpoint returns results from all layers
- Similarity-based ranking across different types

✅ **Configurable search parameters**
- `p_limit`: Max results to return (default: 20)
- `p_threshold`: Minimum similarity score (default: 0.7)
- Results sorted by similarity descending

✅ **Rich metadata**
- Each result includes type, title, description, similarity
- Type-specific metadata (agent for sessions, status for tasks, etc.)
- Excludes archived items automatically

### Database Changes

**New Functions:** 1
- `search_all_memory_semantic(p_query_embedding, p_limit, p_threshold)`

**Modified Tables:** 0 (no schema changes)

**Total Size:** ~5 KB (just the function)

---

## After Migration Success

### Next Steps (Day 4)

1. **Generate Embeddings for Existing Data**
   - Run backfill script: `python/scripts/backfill_embeddings.py`
   - This will populate embedding columns for existing tasks/projects

2. **Test Unified Search**
   - Use API endpoint: `POST /api/sessions/search/all`
   - Verify results from multiple memory layers

3. **Monitor Search Quality**
   - Adjust threshold if needed (0.6-0.8 typical range)
   - Review result ranking and relevance

### Test the Function

Once embeddings are populated, test with:

```sql
-- Get a sample embedding to use as query
WITH sample_embedding AS (
    SELECT embedding
    FROM archon_sessions
    WHERE embedding IS NOT NULL
    LIMIT 1
)
SELECT *
FROM search_all_memory_semantic(
    (SELECT embedding FROM sample_embedding),
    10,   -- limit
    0.5   -- threshold
);
```

---

## Troubleshooting

### Error: "relation archon_sessions does not exist"

**Problem:** Migration 002 not run

**Solution:**
```bash
# Run migration 002 first
psql "$DATABASE_URL" -f migration/002_session_memory.sql
```

### Error: "type vector does not exist"

**Problem:** pgvector extension not enabled

**Solution:**
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Error: "function already exists"

**Status:** ✅ Safe to ignore

The migration uses `CREATE OR REPLACE FUNCTION` so it's idempotent.

---

## Success Indicators

You'll know the migration succeeded if:

- ✅ No errors in SQL Editor
- ✅ Function exists in pg_proc table
- ✅ Migration record inserted in archon_migrations
- ✅ NOTICE message shows "Migration 003: COMPLETE"

**If ALL checks pass:** Migration successful! ✅

**Progress:** 80% → 82% (+2% - unified search function)

---

## Rollback (If Needed)

If you need to undo this migration:

```sql
-- Drop the function
DROP FUNCTION IF EXISTS search_all_memory_semantic;

-- Remove from migrations table
DELETE FROM archon_migrations WHERE version = '003';
```

---

## Summary

**Migration:** 003_unified_memory_search.sql
**Status:** Ready to run
**Method:** Supabase Dashboard (recommended) or psql
**Time:** 2 minutes
**Risk:** Very low (no schema changes, idempotent)
**Next:** Generate embeddings for existing data

**You are ready to run this migration!** 🚀

---

**Created By:** Claude (Archon Agent)
**Date:** 2026-02-14
**Project:** Shared Memory System Implementation
**Phase:** Phase 2, Day 4
