# Phase 2, Task 91: Conversation History Table Migration

**Task**: Create conversation_history with Vector Embeddings
**Task ID**: 0564a09e-0481-4c8d-9802-3eb6e066a4c5
**Date**: 2026-02-18
**Status**: Migration Created - Pending Application

## Migration Overview

**File**: `migration/004_conversation_history.sql`
**Purpose**: Add conversation message tracking with vector embeddings
**Dependencies**: Migration 002 (archon_sessions table)

## Migration Contents

### 1. Table Schema ✅

```sql
CREATE TABLE conversation_history (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES archon_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) CHECK (role IN ('user', 'assistant', 'system')),
    message TEXT NOT NULL,
    tools_used JSONB DEFAULT '[]',
    type VARCHAR(50),
    subtype VARCHAR(50),
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);
```

**Columns**:
- ✅ `id` - UUID primary key
- ✅ `session_id` - Foreign key to archon_sessions
- ✅ `role` - Message role (user/assistant/system)
- ✅ `message` - Message content
- ✅ `tools_used` - JSON array of tools used
- ✅ `type` - MeshOS taxonomy type
- ✅ `subtype` - MeshOS taxonomy subtype
- ✅ `embedding` - VECTOR(1536) for semantic search
- ✅ `created_at` - Timestamp
- ✅ `metadata` - Additional JSON metadata

### 2. Indexes ✅

| Index Name | Column(s) | Type | Purpose |
|------------|-----------|------|---------|
| `idx_conversation_session_id` | session_id | B-tree | Session lookups |
| `idx_conversation_role` | role | B-tree | Role filtering |
| `idx_conversation_created_at` | created_at DESC | B-tree | Chronological queries |
| `idx_conversation_type` | type, subtype | B-tree | Taxonomy filtering |
| `idx_conversation_embedding` | embedding | ivfflat | Vector similarity search |

**Vector Index Configuration**:
- Algorithm: ivfflat with cosine distance
- Lists: 100 (suitable for 10k-100k rows)
- Distance: `<=>` cosine operator

### 3. Trigger Placeholder ✅

**Function**: `trigger_conversation_embedding_placeholder()`
**Purpose**: Reserved for future auto-embedding generation
**Current Behavior**: Pass-through (no-op)
**Future Use**:
- Queue embedding generation jobs
- Update metadata with processing status
- Enforce embedding policies

### 4. Helper Functions ✅

#### get_conversation_history(session_id, limit)
Retrieve conversation history in chronological order.

```sql
SELECT * FROM get_conversation_history(
    'session-uuid-here',
    100
);
```

#### search_conversation_semantic(query_embedding, session_id, match_count, threshold)
Semantic search across conversations.

```sql
SELECT * FROM search_conversation_semantic(
    query_embedding_vector,
    NULL,  -- All sessions
    10,    -- Top 10 results
    0.7    -- 70% similarity threshold
);
```

#### get_recent_conversation_messages(session_id, count)
Get N most recent messages for a session.

```sql
SELECT * FROM get_recent_conversation_messages(
    'session-uuid-here',
    10
);
```

#### count_messages_by_role(session_id)
Statistics on message distribution by role.

```sql
SELECT * FROM count_messages_by_role('session-uuid-here');
```

### 5. Views ✅

#### v_recent_conversations
Recent messages from last 7 days across all sessions.

```sql
SELECT * FROM v_recent_conversations LIMIT 20;
```

#### v_conversation_stats
Conversation statistics per session.

```sql
SELECT * FROM v_conversation_stats
WHERE total_messages > 10
ORDER BY last_message_at DESC;
```

### 6. Row-Level Security ✅

- RLS enabled on conversation_history table
- Service role: Full access
- Authenticated users: Read access

### 7. Sample Data ✅

Migration includes 4 sample messages for testing:
- 2 user messages (command, question)
- 2 assistant messages (responses with tools_used)
- MeshOS taxonomy examples (type/subtype)

## Application Instructions

### Step 1: Access Supabase SQL Editor

1. Go to: https://supabase.com/dashboard/project/vrxaidusyfpkebjcvpfo/sql
2. Click "New query"

### Step 2: Run Migration

Copy and paste the contents of `migration/004_conversation_history.sql` into the SQL editor and execute.

### Step 3: Verify Application

Expected output:
```
NOTICE: Created sample session: <uuid>
NOTICE: Inserted 4 sample conversation messages
NOTICE: Migration 004: COMPLETE
```

## Verification Tests

After applying the migration, run these verification queries:

### Test 1: Table Exists
```sql
SELECT COUNT(*) FROM conversation_history;
```
Expected: At least 4 rows (sample data)

### Test 2: Indexes Created
```sql
SELECT indexname FROM pg_indexes
WHERE tablename = 'conversation_history';
```
Expected: 5 indexes

### Test 3: Helper Function
```sql
SELECT * FROM get_conversation_history(
    (SELECT id FROM archon_sessions LIMIT 1),
    10
);
```
Expected: 4 sample messages

### Test 4: View Access
```sql
SELECT * FROM v_recent_conversations LIMIT 5;
```
Expected: Sample messages visible

### Test 5: Count by Role
```sql
SELECT * FROM count_messages_by_role(
    (SELECT id FROM archon_sessions LIMIT 1)
);
```
Expected:
- user: 2
- assistant: 2

## Acceptance Criteria Assessment

### ✅ Table with vector column created
- Status: COMPLETE
- conversation_history table schema includes VECTOR(1536) embedding column

### ✅ ivfflat index added for embeddings
- Status: COMPLETE
- idx_conversation_embedding created with ivfflat using vector_cosine_ops

### ✅ Trigger placeholder created
- Status: COMPLETE
- trigger_conversation_embedding_placeholder() function and trigger created
- Reserved for future auto-embedding generation

### ✅ MeshOS taxonomy fields included
- Status: COMPLETE
- `type` and `subtype` columns added
- Sample data demonstrates taxonomy usage

### ✅ Test queries run successfully
- Status: PENDING APPLICATION
- Queries ready in SECTION 9 of migration file
- Will verify after migration is applied

## Schema Comparison

### archon_session_events vs conversation_history

| Aspect | archon_session_events | conversation_history |
|--------|----------------------|---------------------|
| Purpose | Generic event logging | LLM conversation messages |
| Key Column | event_type | role |
| Content | event_data (JSONB) | message (TEXT) |
| Use Case | Task updates, actions | User/Assistant dialogue |
| Example | "task_completed" | "Create a migration" |

**Both tables**:
- Link to archon_sessions
- Support vector embeddings
- Store metadata as JSONB
- Include timestamps

## Integration Points

### Backend Service
Will need to create/update:
- `python/src/server/services/conversation_service.py` (new)
- Or extend `python/src/server/services/session_service.py`

### API Endpoints
Suggested endpoints:
- `POST /api/sessions/{id}/messages` - Add message
- `GET /api/sessions/{id}/messages` - Get conversation
- `POST /api/conversations/search` - Semantic search

### MCP Tools
Per project plan:
- `store_conversation_message` - Save user/assistant message
- `get_session_history` - Retrieve conversation
- `search_conversation_history` - Semantic search

## Next Steps

1. **Apply Migration** ⚠️ REQUIRED
   - Run migration in Supabase SQL editor
   - Verify success via NOTICE messages

2. **Run Verification Tests**
   - Execute all 5 test queries
   - Confirm expected results

3. **Update Task Status**
   - Mark task 91 as "done" after verification

4. **Backend Integration** (Future Tasks)
   - Create conversation service
   - Add API endpoints
   - Implement MCP tools

## Related Files

- **Migration**: `migration/004_conversation_history.sql`
- **Session Migration**: `migration/002_session_memory.sql`
- **Project Plan**: `migration/shared_memory_project.sql`
- **Phase 1 Summary**: `docs/PHASE_1_COMPLETION_SUMMARY.md`

---

**Created By**: Claude (Archon Agent)
**Creation Date**: 2026-02-18
**Task Status**: Migration Created - Ready for Application
**Next Action**: Apply migration via Supabase SQL editor
