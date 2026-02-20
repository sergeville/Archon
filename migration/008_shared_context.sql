CREATE TABLE IF NOT EXISTS archon_shared_context (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  context_key TEXT UNIQUE NOT NULL,
  value JSONB NOT NULL DEFAULT '{}',
  set_by TEXT NOT NULL,
  session_id UUID REFERENCES archon_sessions(id) ON DELETE SET NULL,
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS archon_shared_context_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  context_key TEXT NOT NULL,
  old_value JSONB,
  new_value JSONB NOT NULL,
  changed_by TEXT NOT NULL,
  changed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger to auto-populate history on update
CREATE OR REPLACE FUNCTION archon_shared_context_audit() RETURNS trigger AS $$
BEGIN
  INSERT INTO archon_shared_context_history(context_key, old_value, new_value, changed_by)
  VALUES (NEW.context_key, OLD.value, NEW.value, NEW.set_by);
  NEW.updated_at := NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS shared_context_audit_trigger ON archon_shared_context;
CREATE TRIGGER shared_context_audit_trigger
  BEFORE UPDATE ON archon_shared_context
  FOR EACH ROW EXECUTE FUNCTION archon_shared_context_audit();

CREATE INDEX IF NOT EXISTS idx_shared_context_key ON archon_shared_context(context_key);
CREATE INDEX IF NOT EXISTS idx_shared_context_history_key ON archon_shared_context_history(context_key);

ALTER TABLE archon_shared_context ENABLE ROW LEVEL SECURITY;
ALTER TABLE archon_shared_context_history ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'archon_shared_context' AND policyname = 'Service role full access'
  ) THEN
    CREATE POLICY "Service role full access" ON archon_shared_context
      FOR ALL USING (auth.role() = 'service_role');
  END IF;
END $$;
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'archon_shared_context_history' AND policyname = 'Service role full access'
  ) THEN
    CREATE POLICY "Service role full access" ON archon_shared_context_history
      FOR ALL USING (auth.role() = 'service_role');
  END IF;
END $$;
