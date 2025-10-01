-- Add quote_id column to quotes table if it doesn't exist
-- Run this in Supabase SQL Editor if you're getting quote_id column errors

-- Check if quote_id column exists and add it if missing
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'quotes' 
        AND column_name = 'quote_id'
    ) THEN
        ALTER TABLE quotes ADD COLUMN quote_id TEXT;
        CREATE INDEX IF NOT EXISTS idx_quotes_quote_id ON quotes(quote_id);
        RAISE NOTICE 'Added quote_id column to quotes table';
    ELSE
        RAISE NOTICE 'quote_id column already exists in quotes table';
    END IF;
END $$;

-- Verify the column was added
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'quotes'
ORDER BY ordinal_position;
