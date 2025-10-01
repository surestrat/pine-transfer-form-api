-- Diagnostic queries to check Supabase database schema
-- Run these in Supabase SQL Editor to diagnose issues

-- 1. Check if tables exist
SELECT 
    table_name,
    table_type
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('quotes', 'leads')
ORDER BY table_name;

-- 2. Check all columns in quotes table
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'quotes'
ORDER BY ordinal_position;

-- 3. Check all columns in leads table
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'leads'
ORDER BY ordinal_position;

-- 4. Check indexes on quotes
SELECT 
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'quotes'
ORDER BY indexname;

-- 5. Check indexes on leads
SELECT 
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'leads'
ORDER BY indexname;

-- 6. Check RLS policies
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd
FROM pg_policies
WHERE tablename IN ('quotes', 'leads')
ORDER BY tablename, policyname;

-- 7. Count records in each table
SELECT 'quotes' as table_name, COUNT(*) as record_count FROM quotes
UNION ALL
SELECT 'leads' as table_name, COUNT(*) as record_count FROM leads;
