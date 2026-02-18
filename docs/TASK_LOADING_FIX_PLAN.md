# Task Loading Fix Plan - Shared Memory Project

## Problem Analysis

### Root Cause
The SQL file `migration/shared_memory_project.sql` cannot be loaded because:
1. **Script expects local PostgreSQL**: Uses `psql "$SUPABASE_URL"`
2. **Supabase URL is REST API**: `https://vrxaidusyfpkebjcvpfo.supabase.co` (not a psql connection string)
3. **Missing DB connection string**: Need `postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres`

### SQL File Details
- **Size**: 1,337 lines
- **Task Count**: 64 INSERT statements
- **Structure**: Uses CTEs (Common Table Expressions) for project reference
- **Complexity**: Advanced SQL with JSONB, arrays, and WITH clauses

### Current State
- ✅ psql installed: `/usr/local/bin/psql`
- ✅ Supabase credentials available
- ❌ Direct database connection string not configured
- ❌ Tasks not loaded (project exists but has 0 tasks)

## Solution Approaches

### Option 1: Get Supabase Direct Connection String ⭐ RECOMMENDED
**Effort**: 5 minutes
**Reliability**: HIGH
**One-time setup**: YES

**Steps**:
1. Go to Supabase Dashboard: https://supabase.com/dashboard/project/vrxaidusyfpkebjcvpfo
2. Navigate to: Project Settings → Database → Connection String
3. Copy "Connection string" (URI format)
4. Add to `.env` as `SUPABASE_DATABASE_URL`
5. Update load script to use `psql "$SUPABASE_DATABASE_URL"`
6. Run: `./scripts/load_shared_memory_project.sh`

**Pros**:
- Uses existing SQL file (no conversion needed)
- Fast execution (single transaction)
- Preserves complex SQL structure (CTEs, arrays, JSONB)
- Can be reused for other migrations

**Cons**:
- Requires Supabase dashboard access
- Need to store database password in .env

---

### Option 2: Python Script Using Supabase Client
**Effort**: 30-45 minutes
**Reliability**: HIGH
**Reusable**: YES

**Implementation**:
Create `scripts/load_tasks_via_api.py` that:
1. Connects to Supabase using existing service key
2. Reads and parses SQL file
3. Extracts task data from INSERT statements
4. Creates tasks via Supabase client

**Pros**:
- Uses existing credentials (no new secrets)
- Works with cloud Supabase
- Can add validation and error handling
- Reusable for future task imports

**Cons**:
- Need to parse SQL (or maintain parallel Python data structure)
- More complex than direct SQL execution
- Slower than bulk SQL (individual inserts)

---

### Option 3: Convert SQL to JSON + API Loader
**Effort**: 1-2 hours
**Reliability**: MEDIUM
**Maintenance**: HIGH

**Implementation**:
1. Convert SQL file to JSON structure
2. Create loader script that reads JSON
3. Use Archon REST API to create tasks

**Pros**:
- Human-readable task definitions
- Easy to edit/maintain
- No SQL parsing needed

**Cons**:
- Need to maintain two formats (SQL + JSON)
- API has rate limits
- Slower (HTTP overhead per task)
- Already tried this - had validation issues

---

### Option 4: Bulk Import via Supabase REST API
**Effort**: 45-60 minutes
**Reliability**: MEDIUM
**Performance**: GOOD

**Implementation**:
1. Parse SQL file to extract task data
2. Use Supabase REST API bulk insert
3. Single HTTP request with all 64 tasks

**Pros**:
- Fast (single bulk insert)
- Uses existing credentials
- No database connection needed

**Cons**:
- Need to parse SQL file
- API payload size limits
- Less control over transaction

---

### Option 5: Docker-based psql Execution
**Effort**: 20-30 minutes
**Reliability**: HIGH
**Isolation**: GOOD

**Implementation**:
1. Create temporary Docker container with psql
2. Mount SQL file as volume
3. Execute via container with Supabase connection string

**Pros**:
- Clean environment
- No local psql version issues
- Can be scripted

**Cons**:
- Requires Docker
- Still needs database connection string
- Overkill for this use case

---

## Recommended Solution: Option 1 (Direct Connection)

### Why Option 1?
1. **Fastest to implement** - Just need connection string
2. **Most reliable** - Direct SQL execution
3. **Preserves SQL structure** - No conversion needed
4. **Reusable** - Works for all future migrations

### Implementation Plan

#### Step 1: Get Database Connection String (User Action Required)
```
1. Visit: https://supabase.com/dashboard/project/vrxaidusyfpkebjcvpfo/settings/database
2. Look for "Connection string" section
3. Select "URI" format
4. Copy the string (format: postgresql://postgres:[password]@...)
5. Note: Password should already be filled in
```

#### Step 2: Add to Environment
```bash
# Add to ~/Documents/Projects/Archon/.env
SUPABASE_DATABASE_URL="postgresql://postgres:[password]@db.vrxaidusyfpkebjcvpfo.supabase.co:5432/postgres"
```

#### Step 3: Update Load Script
```bash
# Edit scripts/load_shared_memory_project.sh
# Change line 60 from:
if psql "$SUPABASE_URL" -f migration/shared_memory_project.sql; then

# To:
if psql "$SUPABASE_DATABASE_URL" -f migration/shared_memory_project.sql; then
```

#### Step 4: Execute
```bash
cd ~/Documents/Projects/Archon
./scripts/load_shared_memory_project.sh
```

#### Expected Output
```
✅ Project loaded successfully!
✅ Project created: 'Shared Memory System Implementation'
✅ Tasks created: 64
```

---

## Fallback: Option 2 (Python Script)

If Option 1 fails or connection string not accessible, implement Option 2.

### Quick Implementation
```python
#!/usr/bin/env python3
"""Load tasks from SQL file via Supabase client"""
import re
from pathlib import Path
from supabase import create_client

# Read SQL file
sql_content = Path("migration/shared_memory_project.sql").read_text()

# Get project ID
project_id = "7c3528df-b1a2-4fde-9fee-68727c15b6c6"

# Parse tasks (simplified - real implementation needs robust parsing)
task_pattern = r"INSERT INTO archon_tasks.*?VALUES.*?\((.*?)\);"
matches = re.findall(task_pattern, sql_content, re.DOTALL)

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Insert tasks
for task_data in parsed_tasks:
    supabase.table("archon_tasks").insert(task_data).execute()
```

---

## Testing Plan

After loading tasks:

### 1. Verify Task Count
```bash
curl -s http://localhost:8181/api/projects/7c3528df-b1a2-4fde-9fee-68727c15b6c6/tasks | jq 'length'
# Expected: 64
```

### 2. Check Task Statuses
```bash
curl -s http://localhost:8181/api/tasks | jq '[.tasks[] | select(.project_id == "7c3528df-b1a2-4fde-9fee-68727c15b6c6")] | group_by(.status) | map({status: .[0].status, count: length})'
# Expected: All "todo" status
```

### 3. Verify in UI
- Open http://localhost:3737
- Navigate to Projects → "Shared Memory System Implementation"
- Should see 64 tasks organized by phase

### 4. Test MCP Tools
```python
# Via Claude Code or MCP client
find_tasks(filter_by="project", filter_value="7c3528df-b1a2-4fde-9fee-68727c15b6c6")
# Should return all 64 tasks
```

---

## Risk Assessment

### Option 1 Risks: LOW
- ✅ Database connection string should be available in Supabase dashboard
- ✅ psql is already installed
- ⚠️ Password might need to be reset if not known

### Option 2 Risks: MEDIUM
- ⚠️ SQL parsing complexity
- ⚠️ JSONB and array handling in Python
- ✅ Can be tested incrementally

### Mitigation
1. Try Option 1 first (5 min attempt)
2. If blocked, switch to Option 2
3. Create reusable solution for future imports

---

## Success Criteria

✅ All 64 tasks loaded into database
✅ Tasks linked to correct project ID
✅ Task metadata preserved (phase, week, estimates)
✅ Task order preserved (100 down to 1)
✅ Tags properly structured
✅ Visible in Archon UI
✅ Accessible via MCP tools
✅ Can be filtered by phase/week/status

---

## Timeline

**Option 1**: 5-10 minutes (if connection string available)
**Option 2**: 45-60 minutes (development + testing)
**Option 3**: 2-3 hours (not recommended)

**Recommended Path**: Try Option 1 immediately, fall back to Option 2 if needed.

---

## Next Steps

1. **User Action Required**: Get Supabase database connection string from dashboard
2. **Claude Action**: Update load script with new env variable
3. **Execution**: Run updated script
4. **Validation**: Verify 64 tasks loaded successfully
5. **Documentation**: Update project docs with working approach

---

**Created**: 2026-02-18
**Project**: Shared Memory System Implementation
**Issue**: Task loading from SQL file
**Status**: Plan ready, awaiting implementation
