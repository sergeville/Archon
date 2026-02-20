-- Fix embedding column dimensions from VECTOR(1536) to VECTOR(1024)
-- Required because the current Ollama mxbai-embed-large model produces 1024-dimensional embeddings,
-- not 1536 (OpenAI standard). Must be run before any embedding generation works.

-- Drop ivfflat indexes first (they bind to a specific dimension)
DROP INDEX IF EXISTS idx_sessions_embedding;
DROP INDEX IF EXISTS idx_events_embedding;
DROP INDEX IF EXISTS idx_tasks_embedding;
DROP INDEX IF EXISTS idx_projects_embedding;

-- Alter embedding columns to 1024 dimensions
ALTER TABLE archon_sessions ALTER COLUMN embedding TYPE VECTOR(1024) USING NULL;
ALTER TABLE archon_session_events ALTER COLUMN embedding TYPE VECTOR(1024) USING NULL;
ALTER TABLE archon_tasks ALTER COLUMN embedding TYPE VECTOR(1024) USING NULL;
ALTER TABLE archon_projects ALTER COLUMN embedding TYPE VECTOR(1024) USING NULL;

-- Recreate ivfflat indexes with correct dimensions
CREATE INDEX IF NOT EXISTS idx_sessions_embedding ON archon_sessions
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_events_embedding ON archon_session_events
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_tasks_embedding ON archon_tasks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_projects_embedding ON archon_projects
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
