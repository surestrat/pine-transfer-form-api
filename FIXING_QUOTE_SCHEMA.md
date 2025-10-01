# Fixing Quote Service Schema Error

## Problem
You're getting this error:
```json
{
  "error": {
    "message": "Could not find the 'quote_id' column of 'quotes' in the schema cache"
  }
}
```

## Diagnosis

The `quote_id` column is defined in the schema but might not exist in your actual Supabase database.

## Solution Steps

### Step 1: Check Database Schema

1. Go to your Supabase dashboard: https://supa.usa-solarenergy.com
2. Click on **SQL Editor**
3. Copy and paste the contents of `check_supabase_schema.sql`
4. Click **Run**
5. Review the results to see:
   - If `quotes` table exists
   - What columns the `quotes` table has
   - If `quote_id` column is present

### Step 2A: If Tables Don't Exist

If you see that the tables don't exist at all:

1. In Supabase SQL Editor
2. Copy and paste the **entire contents** of `supabase_setup.sql`
3. Click **Run**
4. This will create both `quotes` and `leads` tables with all columns

### Step 2B: If Tables Exist but `quote_id` Column is Missing

If the `quotes` table exists but doesn't have the `quote_id` column:

1. In Supabase SQL Editor
2. Copy and paste the contents of `add_quote_id_column.sql`
3. Click **Run**
4. This will add the missing `quote_id` column

### Step 3: Test the API

After running the SQL fixes, test the quote endpoint:

```bash
# Start the server (if not already running)
python run.py

# In another terminal, test the quote endpoint
curl -X POST http://localhost:4000/api/v1/quote \
  -H "Content-Type: application/json" \
  -d '{
    "source": "SureStrat",
    "externalReferenceId": "TEST-'$(date +%s)'",
    "vehicles": [{
      "make": "Toyota",
      "model": "Corolla",
      "year": 2020,
      "mmCode": "TCOR20",
      "value": 250000,
      "coverType": "comprehensive"
    }],
    "agentEmail": "test@surestrat.co.za",
    "agentBranch": "Test Branch"
  }'
```

## Expected Result

You should see a successful response like:
```json
{
  "premium": 1234.56,
  "excess": 5000,
  "quoteId": null
}
```

## Additional Notes

- The `quote_id` field stores the ID returned by Pineapple API (optional)
- Transfers are working fine because the `leads` table was set up correctly
- The issue is specific to the `quotes` table schema

## Files Reference

- `supabase_setup.sql` - Complete database setup (creates tables from scratch)
- `add_quote_id_column.sql` - Adds missing quote_id column only
- `check_supabase_schema.sql` - Diagnostic queries to check schema

## Temporary Workaround

I've already commented out the `quote_id` update in the code, so quotes will work even without this column. However, it's better to add the column for future use.
