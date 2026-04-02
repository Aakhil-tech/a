-- Run this in your Supabase SQL editor
ALTER TABLE logs
  ADD COLUMN IF NOT EXISTS risk_level TEXT DEFAULT 'low',
  ADD COLUMN IF NOT EXISTS compliance_tags JSONB DEFAULT '[]',
  ADD COLUMN IF NOT EXISTS compliance_violations JSONB DEFAULT '[]',
  ADD COLUMN IF NOT EXISTS reasoning TEXT,
  ADD COLUMN IF NOT EXISTS session_id TEXT,
  ADD COLUMN IF NOT EXISTS decision_id TEXT;
