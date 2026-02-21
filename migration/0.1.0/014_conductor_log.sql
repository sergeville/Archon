-- =====================================================
-- Phase 3: Conductor Log
-- Migration 012: Conductor Reasoning Log Table
-- =====================================================
-- Date: 2026-02-21
-- Author: Claude (Archon Agent)
-- Purpose: Centralized log for Conductor (Gemini/Claude) delegation reasoning
-- Project: Orchestration Elaboration Plan — Phase 3
-- =====================================================

-- =====================================================
-- SECTION 1: CONDUCTOR REASONING LOG TABLE
-- =====================================================

-- conductor_reasoning_log Table
-- Records the Conductor's internal reasoning for each delegation decision:
-- why a particular sub-agent was chosen, what context was injected, and
-- what factors drove the delegation. Outcome is filled in after execution.
CREATE TABLE IF NOT EXISTS conductor_reasoning_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    work_order_id TEXT NOT NULL,
    mission_id TEXT,
    conductor_agent TEXT NOT NULL,
    delegation_target TEXT NOT NULL,
    reasoning TEXT NOT NULL,
    context_injected JSONB DEFAULT '{}',
    decision_factors JSONB DEFAULT '[]',
    confidence_score FLOAT CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    outcome TEXT CHECK (outcome IN ('success', 'failure', 'partial') OR outcome IS NULL),
    outcome_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- =====================================================
-- SECTION 2: INDEXES FOR PERFORMANCE
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_conductor_log_work_order ON conductor_reasoning_log(work_order_id);
CREATE INDEX IF NOT EXISTS idx_conductor_log_mission ON conductor_reasoning_log(mission_id);
CREATE INDEX IF NOT EXISTS idx_conductor_log_conductor ON conductor_reasoning_log(conductor_agent);
CREATE INDEX IF NOT EXISTS idx_conductor_log_created ON conductor_reasoning_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conductor_log_outcome ON conductor_reasoning_log(outcome);

-- =====================================================
-- SECTION 3: TRIGGER FOR AUTO-UPDATE OF updated_at
-- =====================================================

-- Trigger function dedicated to this table (follows 002 pattern of naming
-- the function after the table to keep each trigger self-contained)
CREATE OR REPLACE FUNCTION conductor_log_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_conductor_reasoning_log_updated_at
    BEFORE UPDATE ON conductor_reasoning_log
    FOR EACH ROW
    EXECUTE FUNCTION conductor_log_updated_at();

-- =====================================================
-- SECTION 4: ROW LEVEL SECURITY (RLS)
-- =====================================================

ALTER TABLE conductor_reasoning_log ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'conductor_reasoning_log'
          AND policyname = 'Allow service role full access on conductor_reasoning_log'
    ) THEN
        CREATE POLICY "Allow service role full access on conductor_reasoning_log"
            ON conductor_reasoning_log
            FOR ALL USING (auth.role() = 'service_role');
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'conductor_reasoning_log'
          AND policyname = 'Allow authenticated users on conductor_reasoning_log'
    ) THEN
        CREATE POLICY "Allow authenticated users on conductor_reasoning_log"
            ON conductor_reasoning_log
            FOR ALL TO authenticated USING (true);
    END IF;
END $$;

-- =====================================================
-- SECTION 5: HELPER VIEWS
-- =====================================================

-- View: Delegation stats per conductor and target
CREATE OR REPLACE VIEW v_conductor_delegation_stats AS
SELECT
    conductor_agent,
    delegation_target,
    COUNT(*) AS total_delegations,
    ROUND(AVG(confidence_score)::NUMERIC, 3) AS avg_confidence,
    COUNT(*) FILTER (WHERE outcome = 'success') AS successes,
    COUNT(*) FILTER (WHERE outcome = 'failure') AS failures,
    COUNT(*) FILTER (WHERE outcome = 'partial') AS partials,
    COUNT(*) FILTER (WHERE outcome IS NULL) AS pending,
    ROUND(
        (COUNT(*) FILTER (WHERE outcome = 'success')::FLOAT /
         NULLIF(COUNT(*) FILTER (WHERE outcome IS NOT NULL), 0) * 100)::NUMERIC,
        1
    ) AS success_rate_pct
FROM conductor_reasoning_log
GROUP BY conductor_agent, delegation_target
ORDER BY conductor_agent, total_delegations DESC;

-- =====================================================
-- SECTION 6: COLUMN DOCUMENTATION
-- =====================================================

COMMENT ON TABLE conductor_reasoning_log IS 'Records the Conductor agent reasoning behind each delegation decision. One row per delegation event within a Work Order.';

COMMENT ON COLUMN conductor_reasoning_log.work_order_id IS 'Work Order identifier this delegation belongs to (TEXT, not enforced FK — Work Orders live in a separate store)';
COMMENT ON COLUMN conductor_reasoning_log.mission_id IS 'Optional mission or parent task identifier for grouping related work orders';
COMMENT ON COLUMN conductor_reasoning_log.conductor_agent IS 'Which agent acted as Conductor for this delegation (e.g. claude, gemini)';
COMMENT ON COLUMN conductor_reasoning_log.delegation_target IS 'Which sub-agent type was selected for this task (e.g. claude_code, gemini_pro, gpt4)';
COMMENT ON COLUMN conductor_reasoning_log.reasoning IS 'Full natural-language reasoning text explaining why this delegation was made';
COMMENT ON COLUMN conductor_reasoning_log.context_injected IS 'JSON object describing which context slices were injected into the sub-agent prompt';
COMMENT ON COLUMN conductor_reasoning_log.decision_factors IS 'JSON array of factors that drove the delegation decision (e.g. agent capability, task type, load)';
COMMENT ON COLUMN conductor_reasoning_log.confidence_score IS 'Conductor self-reported confidence in this delegation (0.0 = none, 1.0 = certain)';
COMMENT ON COLUMN conductor_reasoning_log.outcome IS 'Execution outcome filled after the delegated task completes: success, failure, or partial';
COMMENT ON COLUMN conductor_reasoning_log.outcome_notes IS 'Free-text notes on the outcome — error details, partial results, lessons learned';

-- =====================================================
-- SECTION 7: MIGRATION TRACKING
-- =====================================================

INSERT INTO archon_migrations (version, migration_name)
VALUES ('0.1.0', '014_conductor_log')
ON CONFLICT (version, migration_name) DO NOTHING;

-- =====================================================
-- Migration Complete
-- =====================================================
-- Expected outcomes:
-- - 1 new table (conductor_reasoning_log)
-- - 5 indexes for query performance
-- - 1 trigger function + 1 trigger for updated_at
-- - 2 RLS policies (service role + authenticated)
-- - 1 view (v_conductor_delegation_stats)
--
-- Next steps:
-- 1. Verify table: SELECT * FROM conductor_reasoning_log LIMIT 1;
-- 2. Test view: SELECT * FROM v_conductor_delegation_stats;
-- 3. Wire up conductor_log_api.py in main.py
-- =====================================================
