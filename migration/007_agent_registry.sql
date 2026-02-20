CREATE TABLE IF NOT EXISTS archon_agent_registry (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT UNIQUE NOT NULL,
  capabilities TEXT[] DEFAULT '{}',
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'busy')),
  last_seen TIMESTAMPTZ DEFAULT NOW(),
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_registry_name ON archon_agent_registry(name);
CREATE INDEX IF NOT EXISTS idx_agent_registry_status ON archon_agent_registry(status);

ALTER TABLE archon_agent_registry ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'archon_agent_registry' AND policyname = 'Service role full access'
  ) THEN
    CREATE POLICY "Service role full access" ON archon_agent_registry
      FOR ALL USING (auth.role() = 'service_role');
  END IF;
END $$;
