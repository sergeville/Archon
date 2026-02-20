-- Migration 010: Unified Audit Log
-- Shared timeline for all Archon subsystems (Alfred, Situation Agent, Validation Council, Work Orders)

CREATE TABLE IF NOT EXISTS unified_audit_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    source TEXT NOT NULL,            -- 'archon' | 'alfred' | 'work-orders' | 'council' | 'situation_agent'
    agent TEXT,                      -- which agent or user triggered this
    action TEXT NOT NULL,            -- what happened: 'task_created', 'device_controlled', etc.
    target TEXT,                     -- what was acted on
    risk_level TEXT DEFAULT 'LOW',   -- LOW | MED | HIGH | DESTRUCTIVE
    outcome TEXT,                    -- 'success' | 'failed' | 'blocked' | 'approved'
    metadata JSONB DEFAULT '{}',    -- arbitrary extra data
    session_id TEXT                  -- optional link to Archon session
);

CREATE INDEX IF NOT EXISTS idx_unified_audit_log_timestamp ON unified_audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_unified_audit_log_source ON unified_audit_log(source);
CREATE INDEX IF NOT EXISTS idx_unified_audit_log_risk_level ON unified_audit_log(risk_level);

-- Enable RLS (row-level security) with service role access
ALTER TABLE unified_audit_log ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'unified_audit_log' AND policyname = 'Service role full access'
  ) THEN
    CREATE POLICY "Service role full access" ON unified_audit_log
      FOR ALL USING (auth.role() = 'service_role');
  END IF;
END $$;
