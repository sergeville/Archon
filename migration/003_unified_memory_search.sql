-- =====================================================
-- Migration 003: Unified Memory Search Function
-- =====================================================
-- Purpose: Add database function for unified semantic search across all memory layers
-- Date: 2026-02-14
-- Phase: Phase 2 Day 4
-- Dependencies: Migration 002 (session tables and embedding columns)

-- =====================================================
-- SECTION 1: UNIFIED MEMORY SEARCH FUNCTION
-- =====================================================

CREATE OR REPLACE FUNCTION search_all_memory_semantic(
    p_query_embedding VECTOR(1536),
    p_limit INT DEFAULT 20,
    p_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    type TEXT,
    id UUID,
    title TEXT,
    description TEXT,
    similarity FLOAT,
    created_at TIMESTAMPTZ,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    WITH session_results AS (
        SELECT
            'session'::TEXT as type,
            s.id,
            COALESCE(s.summary, 'Session by ' || s.agent)::TEXT as title,
            NULL::TEXT as description,
            (1 - (s.embedding <=> p_query_embedding))::FLOAT as similarity,
            s.created_at,
            jsonb_build_object(
                'agent', s.agent,
                'project_id', s.project_id,
                'started_at', s.started_at,
                'ended_at', s.ended_at,
                'metadata', s.metadata
            ) as metadata
        FROM archon_sessions s
        WHERE s.embedding IS NOT NULL
          AND (1 - (s.embedding <=> p_query_embedding)) >= p_threshold
    ),
    task_results AS (
        SELECT
            'task'::TEXT as type,
            t.id,
            t.title::TEXT,
            t.description::TEXT,
            (1 - (t.embedding <=> p_query_embedding))::FLOAT as similarity,
            t.created_at,
            jsonb_build_object(
                'status', t.status,
                'assignee', t.assignee,
                'project_id', t.project_id,
                'feature', t.feature,
                'task_order', t.task_order
            ) as metadata
        FROM archon_tasks t
        WHERE t.embedding IS NOT NULL
          AND (1 - (t.embedding <=> p_query_embedding)) >= p_threshold
          AND t.archived = FALSE
    ),
    project_results AS (
        SELECT
            'project'::TEXT as type,
            p.id,
            p.title::TEXT,
            p.description::TEXT,
            (1 - (p.embedding <=> p_query_embedding))::FLOAT as similarity,
            p.created_at,
            jsonb_build_object(
                'features', p.features,
                'completion_percentage', p.completion_percentage,
                'task_count', p.task_count
            ) as metadata
        FROM archon_projects p
        WHERE p.embedding IS NOT NULL
          AND (1 - (p.embedding <=> p_query_embedding)) >= p_threshold
          AND p.archived = FALSE
    )
    SELECT * FROM (
        SELECT * FROM session_results
        UNION ALL
        SELECT * FROM task_results
        UNION ALL
        SELECT * FROM project_results
    ) combined
    ORDER BY similarity DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- SECTION 2: COMMENTS
-- =====================================================

COMMENT ON FUNCTION search_all_memory_semantic IS
    'Unified semantic search across all memory layers (sessions, tasks, projects).
    Returns results from all layers ranked by similarity score.
    Requires embeddings to be generated for records.';

-- =====================================================
-- SECTION 3: RECORD MIGRATION
-- =====================================================

INSERT INTO archon_migrations (version, name, description)
VALUES (
    '003',
    'unified_memory_search',
    'Add unified semantic search function across all memory layers (sessions, tasks, projects). Enables cross-layer similarity search for comprehensive memory retrieval.'
)
ON CONFLICT (version) DO UPDATE SET
    description = EXCLUDED.description,
    applied_at = NOW();

-- =====================================================
-- SECTION 4: VERIFICATION
-- =====================================================

-- Test query (requires embeddings to be populated first)
-- SELECT * FROM search_all_memory_semantic(
--     (SELECT embedding FROM archon_sessions WHERE embedding IS NOT NULL LIMIT 1),
--     10,
--     0.5
-- );

-- =====================================================
-- SECTION 5: SUCCESS SUMMARY
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '
    ========================================
    Migration 003: COMPLETE
    ========================================

    Created:
    - search_all_memory_semantic() function

    Capabilities:
    ✅ Search across sessions, tasks, and projects
    ✅ Unified similarity ranking
    ✅ Configurable threshold and limit
    ✅ Excludes archived items

    Next Steps:
    1. Generate embeddings for existing records
    2. Test unified search endpoint
    3. Verify search quality

    Progress: ~80% → 82% (+2%% - unified search function)
    ========================================
    ';
END $$;
