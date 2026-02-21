-- Migration 013: Add archived_reason column to archon_tasks
-- Zero-downtime migration (nullable column addition)
-- Run in Supabase SQL editor

ALTER TABLE archon_tasks ADD COLUMN IF NOT EXISTS archived_reason TEXT NULL;
