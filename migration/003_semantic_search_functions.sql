-- =====================================================
-- Migration 003: Semantic Search Functions
-- =====================================================
-- Description: Adds database functions for semantic search across tasks and projects
-- Dependencies: Migration 002 (requires embedding columns)
-- Date: 2026-02-14
-- Phase: Phase 2 Day 4
-- =====================================================

-- Function: search_tasks_semantic
-- Search tasks by semantic similarity to a query
CREATE OR REPLACE FUNCTION search_tasks_semantic(
    p_query_embedding VECTOR(1536),
    p_limit INT DEFAULT 10,
    p_threshold FLOAT DEFAULT 0.7,
    p_project_id UUID DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    title VARCHAR,
    description TEXT,
    status VARCHAR,
    priority VARCHAR,
    assignee VARCHAR,
    project_id UUID,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.id,
        t.title,
        t.description,
        t.status,
        t.priority,
        t.assignee,
        t.project_id,
        1 - (t.embedding <=> p_query_embedding) AS similarity
    FROM archon_tasks t
    WHERE
        t.embedding IS NOT NULL
        AND (p_project_id IS NULL OR t.project_id = p_project_id)
        AND (1 - (t.embedding <=> p_query_embedding)) >= p_threshold
    ORDER BY t.embedding <=> p_query_embedding
    LIMIT p_limit;
END;
$$;

-- Function: search_projects_semantic
-- Search projects by semantic similarity to a query
CREATE OR REPLACE FUNCTION search_projects_semantic(
    p_query_embedding VECTOR(1536),
    p_limit INT DEFAULT 10,
    p_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    id UUID,
    title VARCHAR,
    description TEXT,
    features JSONB,
    status VARCHAR,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.title,
        p.description,
        p.features,
        p.status,
        1 - (p.embedding <=> p_query_embedding) AS similarity
    FROM archon_projects p
    WHERE
        p.embedding IS NOT NULL
        AND (1 - (p.embedding <=> p_query_embedding)) >= p_threshold
    ORDER BY p.embedding <=> p_query_embedding
    LIMIT p_limit;
END;
$$;

-- Function: search_all_memory_semantic
-- Unified semantic search across sessions, tasks, and projects
CREATE OR REPLACE FUNCTION search_all_memory_semantic(
    p_query_embedding VECTOR(1536),
    p_limit INT DEFAULT 10,
    p_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    id UUID,
    type VARCHAR,
    title VARCHAR,
    content TEXT,
    similarity FLOAT,
    metadata JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH all_results AS (
        -- Sessions
        SELECT
            s.id,
            'session'::VARCHAR AS type,
            ('Session by ' || s.agent)::VARCHAR AS title,
            COALESCE(s.summary, 'Session in progress')::TEXT AS content,
            1 - (s.embedding <=> p_query_embedding) AS similarity,
            jsonb_build_object(
                'agent', s.agent,
                'started_at', s.started_at,
                'ended_at', s.ended_at,
                'project_id', s.project_id
            ) AS metadata
        FROM archon_sessions s
        WHERE
            s.embedding IS NOT NULL
            AND (1 - (s.embedding <=> p_query_embedding)) >= p_threshold

        UNION ALL

        -- Tasks
        SELECT
            t.id,
            'task'::VARCHAR AS type,
            t.title,
            t.description AS content,
            1 - (t.embedding <=> p_query_embedding) AS similarity,
            jsonb_build_object(
                'status', t.status,
                'priority', t.priority,
                'assignee', t.assignee,
                'project_id', t.project_id
            ) AS metadata
        FROM archon_tasks t
        WHERE
            t.embedding IS NOT NULL
            AND (1 - (t.embedding <=> p_query_embedding)) >= p_threshold

        UNION ALL

        -- Projects
        SELECT
            p.id,
            'project'::VARCHAR AS type,
            p.title,
            p.description AS content,
            1 - (p.embedding <=> p_query_embedding) AS similarity,
            jsonb_build_object(
                'status', p.status,
                'features', p.features
            ) AS metadata
        FROM archon_projects p
        WHERE
            p.embedding IS NOT NULL
            AND (1 - (p.embedding <=> p_query_embedding)) >= p_threshold
    )
    SELECT
        all_results.id,
        all_results.type,
        all_results.title,
        all_results.content,
        all_results.similarity,
        all_results.metadata
    FROM all_results
    ORDER BY similarity DESC
    LIMIT p_limit;
END;
$$;

-- Add comments for documentation
COMMENT ON FUNCTION search_tasks_semantic IS
'Semantic search for tasks using vector similarity. Returns tasks ranked by similarity to query embedding.';

COMMENT ON FUNCTION search_projects_semantic IS
'Semantic search for projects using vector similarity. Returns projects ranked by similarity to query embedding.';

COMMENT ON FUNCTION search_all_memory_semantic IS
'Unified semantic search across all memory layers (sessions, tasks, projects). Returns mixed results ranked by similarity.';
