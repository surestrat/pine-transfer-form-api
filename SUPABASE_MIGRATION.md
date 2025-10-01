# Supabase Migration Guide

This document outlines the migration from Appwrite to Supabase for the Pineapple Integration API.

## Overview

We've migrated from Appwrite to Supabase to leverage PostgreSQL's powerful features, better performance, and more familiar SQL-based queries.

## Key Changes

### 1. Database Backend
- **Before**: Appwrite (NoSQL-like document database)
- **After**: Supabase (PostgreSQL with REST API)

### 2. Data Storage
- **Quotes**: Now stored with JSONB for vehicles (better query performance)
- **Leads**: Same structure but with PostgreSQL native types

### 3. Field Name Changes
Due to PostgreSQL naming conventions, some fields were renamed:

#### Quotes Table
| Appwrite Field | Supabase Field |
|---------------|----------------|
| `internalReference` | `internal_reference` |
| `agentEmail` | `agent_email` |
| `agentBranch` | `agent_branch` |
| `quoteId` | `quote_id` |
| `$id` | `id` (BIGSERIAL) |
| `$createdAt` | `created_at` |
| `$updatedAt` | `updated_at` |

#### Leads Table
| Appwrite Field | Supabase Field |
|---------------|----------------|
| `$id` | `id` (BIGSERIAL) |
| `$createdAt` | `created_at` |
| `$updatedAt` | `updated_at` |

### 4. Code Changes

#### File Structure
```
app/
├── utils/
│   ├── supabase.py (NEW - replaces appwrite.py)
│   └── appwrite.py (REMOVED)
```

#### Updated Files
- `config/settings.py` - Added Supabase configuration
- `app/services/quote.py` - Updated to use Supabase
- `app/services/transfer.py` - Updated to use Supabase
- `app/api/v1/endpoints/quote.py` - Updated field names
- `app/api/v1/endpoints/transfer.py` - Updated field names
- `requirements.txt` - Replaced `appwrite` with `supabase`

## Setup Instructions

### 1. Run SQL Setup in Supabase

1. Log into your Supabase dashboard at https://supa.usa-solarenergy.com
2. Navigate to the SQL Editor
3. Copy and paste the contents of `supabase_setup.sql`
4. Execute the SQL script
5. Verify tables and indexes were created successfully

### 2. Update Environment Variables

Remove Appwrite-related variables and add Supabase configuration:

```bash
# Remove these (no longer needed):
# APPWRITE_API_KEY=...
# APPWRITE_ENDPOINT=...
# APPWRITE_PROJECT_ID=...
# DATABASE_ID=...
# QUOTE_COL_ID=...
# TRANSFER_COL_ID=...

# Add these:
SUPABASE_URL=https://supa.usa-solarenergy.com
SUPABASE_SERVICE_KEY=your_service_role_key_here

# Table names (optional - defaults provided)
QUOTES_TABLE=quotes
TRANSFERS_TABLE=leads
```

### 3. Install Dependencies

```bash
# Remove old dependencies and install new ones
pip uninstall appwrite
pip install -r requirements.txt
```

### 4. Test the Migration

```bash
# Start the API
python run.py

# Test quote endpoint
curl -X POST http://localhost:4000/api/v1/quote \
  -H "Content-Type: application/json" \
  -d '{...}'

# Test transfer endpoint
curl -X POST http://localhost:4000/api/v1/transfer \
  -H "Content-Type: application/json" \
  -d '{...}'
```

## Benefits of Supabase

1. **Better Performance**: PostgreSQL is highly optimized for complex queries
2. **JSONB Support**: Native JSON querying with indexes
3. **Standard SQL**: Familiar syntax and powerful query capabilities
4. **Auto-updating Timestamps**: Triggers handle `updated_at` automatically
5. **Row Level Security**: Built-in security policies
6. **Better Indexing**: Improved query performance with proper indexes
7. **Mature Ecosystem**: Large community and excellent tooling

## API Changes

### Internal Changes Only
The external API contract remains the same - no changes needed for frontend clients.

### Response Structure
- Quote IDs are now integers (not strings)
- Created/updated timestamps use PostgreSQL format
- Vehicles stored as native JSON (not JSON strings)

## Rollback Plan

If you need to rollback to Appwrite:

1. Restore the old environment variables
2. Change `requirements.txt` back to use `appwrite==6.1.0`
3. Revert code changes in git: `git revert <commit-hash>`
4. Restart the API

## Troubleshooting

### Connection Issues
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are correct
- Check network connectivity to Supabase instance
- Ensure Supabase project is active

### Query Errors
- Check field names match the new snake_case convention
- Verify table names are correct in environment variables
- Review Supabase logs in dashboard

### Duplicate Detection Not Working
- Ensure indexes are created on `id_number` and `contact_number`
- Check that the `check_duplicate_transfer` function is working
- Review logs for normalization issues

## Support

For issues or questions:
- Check Supabase logs in the dashboard
- Review application logs with Rich logger
- Contact: zalisiles@surestrat.co.za
