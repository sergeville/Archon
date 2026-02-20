-- =====================================================
-- Pattern Tables: Minimal version (tables only)
-- =====================================================
-- Run this FIRST. No indexes, no triggers, no RLS.
-- This isolates creation from optional features.
-- =====================================================

-- Trigger helper function (safe to run multiple times)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Pattern storage table
CREATE TABLE IF NOT EXISTS archon_patterns (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    pattern_type VARCHAR(50) NOT NULL,
    domain VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    context JSONB DEFAULT '{}',
    action TEXT NOT NULL,
    outcome TEXT,
    embedding VECTOR(1536),
    metadata JSONB DEFAULT '{}',
    created_by VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Pattern observations table
CREATE TABLE IF NOT EXISTS archon_pattern_observations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    pattern_id UUID REFERENCES archon_patterns(id) ON DELETE CASCADE,
    session_id UUID REFERENCES archon_sessions(id) ON DELETE SET NULL,
    observed_at TIMESTAMPTZ DEFAULT NOW(),
    success_rating INT CHECK (success_rating >= 1 AND success_rating <= 5),
    feedback TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Verify tables were created
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('archon_patterns', 'archon_pattern_observations')
ORDER BY table_name;
