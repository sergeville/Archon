-- =====================================================
-- Pattern Tables: Indexes, Function, Trigger, RLS
-- =====================================================
-- Run this AFTER 005_pattern_tables_minimal.sql succeeds.
-- =====================================================

-- Standard indexes
CREATE INDEX IF NOT EXISTS idx_patterns_type ON archon_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_patterns_domain ON archon_patterns(domain);
CREATE INDEX IF NOT EXISTS idx_pattern_obs_pattern ON archon_pattern_observations(pattern_id);
CREATE INDEX IF NOT EXISTS idx_pattern_obs_session ON archon_pattern_observations(session_id);

-- Semantic search function
CREATE OR REPLACE FUNCTION search_patterns_semantic(
    p_query_embedding VECTOR(1536),
    p_limit INT DEFAULT 10,
    p_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    id UUID,
    pattern_type VARCHAR,
    domain VARCHAR,
    description TEXT,
    action TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.pattern_type,
        p.domain,
        p.description,
        p.action,
        1 - (p.embedding <=> p_query_embedding) as similarity
    FROM archon_patterns p
    WHERE p.embedding IS NOT NULL
      AND (1 - (p.embedding <=> p_query_embedding)) > p_threshold
    ORDER BY p.embedding <=> p_query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Auto-update trigger
DROP TRIGGER IF EXISTS update_archon_patterns_updated_at ON archon_patterns;
CREATE TRIGGER update_archon_patterns_updated_at
    BEFORE UPDATE ON archon_patterns
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- RLS
ALTER TABLE archon_patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE archon_pattern_observations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow service role full access on patterns" ON archon_patterns
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Allow authenticated users on patterns" ON archon_patterns
    FOR ALL TO authenticated USING (true);

CREATE POLICY "Allow authenticated users on observations" ON archon_pattern_observations
    FOR ALL TO authenticated USING (true);
