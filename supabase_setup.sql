-- Supabase SQL Setup for Pineapple Integration API
-- Run this in your Supabase SQL Editor

-- ===================================================
-- CREATE LEADS TABLE (for transfers)
-- ===================================================
DROP TABLE IF EXISTS leads CASCADE;

CREATE TABLE leads (
  id BIGSERIAL PRIMARY KEY,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT NOT NULL,
  id_number TEXT,
  quote_id TEXT,
  contact_number TEXT NOT NULL,
  uuid TEXT,
  redirect_url TEXT,
  agent_name TEXT,
  branch_name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  agent_email TEXT,
  imported_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_id_number ON leads(id_number);
CREATE INDEX IF NOT EXISTS idx_leads_contact_number ON leads(contact_number);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at);
CREATE INDEX IF NOT EXISTS idx_leads_branch ON leads(branch_name);
CREATE INDEX IF NOT EXISTS idx_leads_agent ON leads(agent_name);
CREATE INDEX IF NOT EXISTS idx_leads_agent_email ON leads(agent_email);
CREATE INDEX IF NOT EXISTS idx_leads_imported_at ON leads(imported_at);

-- Enable RLS (Row Level Security)
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations for service role
CREATE POLICY "Allow all for service role" ON leads FOR ALL USING (true);

-- ===================================================
-- CREATE QUOTES TABLE
-- ===================================================
DROP TABLE IF EXISTS quotes CASCADE;

CREATE TABLE quotes (
  id BIGSERIAL PRIMARY KEY,
  source TEXT NOT NULL DEFAULT 'SureStrat',
  internal_reference TEXT UNIQUE NOT NULL,
  status TEXT NOT NULL DEFAULT 'PENDING',
  vehicles JSONB NOT NULL,
  premium TEXT,
  excess TEXT,
  quote_id TEXT,
  agent_email TEXT,
  agent_branch TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_quotes_internal_reference ON quotes(internal_reference);
CREATE INDEX IF NOT EXISTS idx_quotes_status ON quotes(status);
CREATE INDEX IF NOT EXISTS idx_quotes_created_at ON quotes(created_at);
CREATE INDEX IF NOT EXISTS idx_quotes_agent_email ON quotes(agent_email);
CREATE INDEX IF NOT EXISTS idx_quotes_quote_id ON quotes(quote_id);

-- Enable RLS (Row Level Security)
ALTER TABLE quotes ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations for service role
CREATE POLICY "Allow all for service role on quotes" ON quotes FOR ALL USING (true);

-- ===================================================
-- CREATE UPDATED_AT TRIGGER FUNCTION
-- ===================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to leads table
CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to quotes table
CREATE TRIGGER update_quotes_updated_at BEFORE UPDATE ON quotes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ===================================================
-- VERIFICATION QUERIES
-- ===================================================
-- Run these to verify your setup:

-- Check tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('leads', 'quotes');

-- Check indexes on leads
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'leads';

-- Check indexes on quotes
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'quotes';

-- Check RLS policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies
WHERE tablename IN ('leads', 'quotes');
