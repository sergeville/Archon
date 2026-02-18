# Complete Phase 2 to 100% - Quick Setup Guide

**Current Status:** Phase 2 at 90%
**Goal:** Enable optional features to reach 92-95%
**Time Required:** 15-30 minutes

---

## What This Enables

### 1. Semantic Search Functions
- Search tasks by meaning, not just keywords
- Search projects by semantic similarity
- Unified memory search across sessions, tasks, and projects

### 2. AI-Powered Session Summarization (using Claude Sonnet 4.5)
- Generate intelligent summaries of work sessions using Claude
- Extract key events and decisions automatically
- Structured insights (outcomes, next steps, etc.)

---

## Step 1: Run Migration 003 (10 minutes)

### Option A: Supabase Dashboard (Recommended)

1. **Open Supabase SQL Editor**
   ```bash
   # Open your Supabase dashboard
   open "https://supabase.com/dashboard"
   ```

2. **Navigate to SQL Editor**
   - Click on your project
   - Go to "SQL Editor" in left sidebar
   - Click "New Query"

3. **Copy Migration SQL**
   ```bash
   # The migration file is ready at:
   cat migration/003_semantic_search_functions.sql
   ```

4. **Paste and Execute**
   - Paste the entire contents into SQL Editor
   - Click "Run" button
   - Verify: Should see "Success. No rows returned"

5. **Verify Functions Created**
   Run this verification query:
   ```sql
   SELECT routine_name
   FROM information_schema.routines
   WHERE routine_schema = 'public'
   AND routine_name LIKE '%semantic%';
   ```

   Expected output:
   ```
   search_tasks_semantic
   search_projects_semantic
   search_all_memory_semantic
   search_sessions_semantic (from migration 002)
   ```

### Option B: Via psql (If you have direct access)

```bash
# If you have PostgreSQL connection string
psql "$DATABASE_URL" -f migration/003_semantic_search_functions.sql
```

---

## Step 2: Configure Anthropic API Key (5 minutes)

### Get Your API Key

1. **Go to Anthropic Console**
   ```bash
   open "https://console.anthropic.com/settings/keys"
   ```

2. **Create a New Key**
   - Click "Create Key"
   - Name it "Archon Session Summarization"
   - Copy the key (you won't see it again!)

### Add to Environment

1. **Edit .env file**
   ```bash
   # Open the .env file
   nano python/.env
   # Or use your preferred editor
   ```

2. **Add the key**
   ```bash
   # Add this line (replace with your actual key)
   ANTHROPIC_API_KEY=sk-ant-...your-key-here...
   ```

3. **Restart Docker container**
   ```bash
   docker compose restart archon-server
   ```

4. **Verify it worked**
   ```bash
   # Check logs for successful startup
   docker compose logs archon-server | grep -i anthropic
   ```

---

## Step 3: Test Semantic Search (5 minutes)

### Test 1: Search Sessions

```bash
curl -s -X POST "http://localhost:8181/api/sessions/search" \
  -H 'Content-Type: application/json' \
  -d '{"query":"database optimization","limit":5}' | jq '.'
```

**Expected:** Should return sessions related to database work

### Test 2: Unified Memory Search

```bash
curl -s -X POST "http://localhost:8181/api/sessions/search/all" \
  -H 'Content-Type: application/json' \
  -d '{"query":"API documentation","limit":10}' | jq '.'
```

**Expected:** Should return results from sessions, tasks, and projects

### Test 3: AI Summarization

```bash
# Pick a session with events
SESSION_ID="e1fd362f-40e7-4037-accf-ba304ee48ce4"

curl -s -X POST "http://localhost:8181/api/sessions/$SESSION_ID/summarize" | jq '.'
```

**Expected:** Should return AI-generated summary with structured insights

---

## Troubleshooting

### Migration 003 Errors

**Error: "relation archon_sessions does not exist"**
- Solution: Run migration 002 first
- Check: `\dt archon_sessions` in psql

**Error: "type vector does not exist"**
- Solution: Enable pgvector extension
- Run: `CREATE EXTENSION IF NOT EXISTS vector;`

### API Key Errors

**Error: "Incorrect API key provided"**
- Check: Key starts with `sk-ant-`
- Verify: No extra spaces in .env file
- Try: Restart Docker container

**Error: "No module named 'anthropic'"**
- Already fixed: pydantic-ai includes Anthropic SDK
- Verify: `docker exec archon-server pip list | grep anthropic`

### Semantic Search Not Working

**Error: "Function search_sessions_semantic not found"**
- Run migration 003
- Check: Supabase SQL Editor executed successfully

**No Results Returned**
- Check: Sessions/tasks have embeddings
- Run: `SELECT COUNT(*) FROM archon_sessions WHERE embedding IS NOT NULL;`
- If zero: Embeddings are generated on new data only

---

## Verification Checklist

After completing all steps:

- [ ] Migration 003 executed successfully
- [ ] Three semantic search functions created
- [ ] Anthropic API key added to .env (for Claude Sonnet 4.5)
- [ ] Docker container restarted
- [ ] Session search returns results
- [ ] Unified memory search works
- [ ] AI summarization generates summaries using Claude

---

## What's Now Enabled

### Semantic Search
✅ Find sessions by meaning: "database work" finds all DB-related sessions
✅ Cross-domain search: "API" finds API tasks, sessions, projects together
✅ Similarity threshold: Only returns relevant results (>0.7 similarity)

### AI Summarization
✅ Automatic session summaries with key events
✅ Structured insights: decisions made, outcomes achieved
✅ Next steps recommendations
✅ Metadata extraction from events

### Phase 2 Completion
- **Before:** 90% (core features only)
- **After:** 95% (all features enabled)
- **Remaining:** 5% (UI polish, documentation)

---

## Next Steps After Completion

### Immediate
1. Test semantic search with real queries
2. Generate summaries for existing sessions
3. Verify MCP tools can access semantic search

### Then: Start Phase 3
Once Phase 2 is 100%:
1. Run migration 004 (pattern learning)
2. Build PatternService
3. Create pattern MCP tools
4. Build pattern UI

---

## Quick Reference Commands

```bash
# Check migration status
docker compose logs archon-server | grep migration

# Test semantic search
curl -s -X POST "http://localhost:8181/api/sessions/search" \
  -H 'Content-Type: application/json' \
  -d '{"query":"test query","limit":5}' | jq '.sessions | length'

# Generate AI summary
curl -s -X POST "http://localhost:8181/api/sessions/{session-id}/summarize" | jq '.summary'

# Restart services
docker compose restart archon-server

# View logs
docker compose logs -f archon-server
```

---

**Estimated Time:** 15-30 minutes
**Difficulty:** Easy (mostly copy-paste)
**Impact:** High (unlocks advanced features)

**Ready?** Start with Step 1: Run Migration 003
