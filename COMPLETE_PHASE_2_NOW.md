# Complete Phase 2 - Action Required

**Status**: Migration 003 SQL is on your clipboard
**Time Required**: 15-20 minutes
**Current Progress**: 90% → 95%

---

## Step 1: Run Migration 003 in Supabase (10 minutes)

### Open Supabase Dashboard

```bash
open "https://supabase.com/dashboard"
```

### Run Migration

1. Select your Archon project in Supabase
2. Go to **SQL Editor** in left sidebar
3. Click **New Query**
4. **Paste** the migration SQL (already in your clipboard)
5. Click **Run**
6. You should see: "Success. No rows returned"

### What This Creates

3 semantic search functions:
- `search_tasks_semantic` - Find tasks by meaning
- `search_projects_semantic` - Find projects by meaning
- `search_all_memory_semantic` - Unified search across sessions/tasks/projects

---

## Step 2: Configure Anthropic API Key (5-10 minutes)

### Get Your API Key

1. Go to: https://console.anthropic.com/settings/keys
2. Click **Create Key**
3. Name it: "Archon Session Summarization"
4. **Copy the key** (starts with `sk-ant-...`)

### Add to Environment

You have two options:

#### Option A: Shell Environment (Quick)

```bash
# Add to ~/.zshrc (or ~/.bashrc)
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key-here"' >> ~/.zshrc

# Reload shell
source ~/.zshrc

# Restart Docker container
docker compose restart archon-server
```

#### Option B: .env File (Recommended)

```bash
# Create .env file in python directory
cat > python/.env << 'EOF'
# Anthropic API for Claude-powered summarization
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional: Remove old OpenAI key
# OPENAI_API_KEY=
EOF

# Restart Docker container
docker compose restart archon-server
```

---

## Step 3: Verify Everything Works (5 minutes)

### Test Migration 003

```bash
~/Documents/.tmp/verify_migration_003.sh
```

Expected output:
```
✅ Session semantic search: WORKING
✅ Unified memory search: WORKING
✅ search_sessions_semantic - EXISTS
✅ search_all_memory_semantic - EXISTS
```

### Test Anthropic API

```bash
# Check API key is set
docker exec archon-server env | grep ANTHROPIC_API_KEY

# Should show: ANTHROPIC_API_KEY=sk-ant-...
```

### Test AI Summarization

```bash
# Pick any session ID from your 23 sessions
SESSION_ID=$(curl -s http://localhost:8181/api/sessions | jq -r '.sessions[0].id')

# Generate AI summary
curl -s -X POST "http://localhost:8181/api/sessions/$SESSION_ID/summarize" | jq '.'
```

Expected: Structured summary with key_events, decisions_made, outcomes, next_steps

---

## Completion Checklist

- [ ] Migration 003 executed in Supabase (3 functions created)
- [ ] Anthropic API key obtained from console.anthropic.com
- [ ] API key added to environment (shell or .env file)
- [ ] Docker container restarted
- [ ] Verification script shows all functions working
- [ ] AI summarization generates Claude-powered summaries

---

## What This Unlocks

### Semantic Search
- Find sessions by meaning: "database optimization" finds all DB work
- Cross-domain search: "API endpoints" finds tasks, sessions, and projects
- Similarity threshold filtering (only returns relevant results)

### AI Summarization
- Automatic session summaries with Claude Sonnet 4.5
- Structured insights: key events, decisions, outcomes
- Next steps recommendations
- High-quality contextual understanding

---

## After Completion

**Phase 2 Status**: 95% complete ✅
**Next Phase**: Pattern Learning (Phase 3)

You'll have:
- ✅ 12 REST API endpoints
- ✅ 5 MCP tools
- ✅ Semantic search across all memory layers
- ✅ AI-powered session insights
- ✅ 23 test sessions
- ✅ Full event logging system

---

## Quick Reference Commands

```bash
# Verify migration 003
~/Documents/.tmp/verify_migration_003.sh

# Check API key in container
docker exec archon-server env | grep ANTHROPIC_API_KEY

# View server logs
docker compose logs -f archon-server

# Restart services
docker compose restart archon-server

# Test summarization
curl -s -X POST "http://localhost:8181/api/sessions/{session-id}/summarize" | jq '.'
```

---

**Ready?** Start with Step 1 - paste the SQL into Supabase (it's already on your clipboard!)
