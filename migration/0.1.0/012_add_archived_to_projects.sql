-- Migration: Add archived column to archon_projects
-- Created: 2026-02-13

ALTER TABLE archon_projects ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT FALSE;

-- Automatically set archived status based on project title
UPDATE archon_projects SET archived = TRUE WHERE title LIKE '[ARCHIVED]%';
UPDATE archon_projects SET archived = FALSE WHERE title NOT LIKE '[ARCHIVED]%';
