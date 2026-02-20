CREATE TABLE IF NOT EXISTS archon_session_handoffs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES archon_sessions(id) ON DELETE CASCADE NOT NULL,
  from_agent TEXT NOT NULL,
  to_agent TEXT NOT NULL,
  context JSONB DEFAULT '{}',
  notes TEXT,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'completed', 'rejected')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  accepted_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_handoffs_session ON archon_session_handoffs(session_id);
CREATE INDEX IF NOT EXISTS idx_handoffs_to_agent ON archon_session_handoffs(to_agent);
CREATE INDEX IF NOT EXISTS idx_handoffs_status ON archon_session_handoffs(status);

ALTER TABLE archon_session_handoffs ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'archon_session_handoffs' AND policyname = 'Service role full access'
  ) THEN
    CREATE POLICY "Service role full access" ON archon_session_handoffs
      FOR ALL USING (auth.role() = 'service_role');
  END IF;
END $$;
