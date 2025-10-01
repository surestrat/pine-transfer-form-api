# Supabase Migration Complete ✅

## Summary of Changes

### 1. **Removed Appwrite Dependencies**
   - ❌ Removed `appwrite==6.1.0` from requirements.txt
   - ✅ Added `supabase==2.8.1` to requirements.txt
   - ❌ Deleted `app/utils/appwrite.py`
   - ✅ Created `app/utils/supabase.py`

### 2. **Updated Configuration**
   - **File**: `config/settings.py`
   - Removed Appwrite settings:
     - `APPWRITE_ENDPOINT`
     - `APPWRITE_PROJECT_ID`
     - `APPWRITE_API_KEY`
     - `DATABASE_ID`
     - `QUOTE_COL_ID`
     - `TRANSFER_COL_ID`
   - Added Supabase settings:
     - `SUPABASE_URL`
     - `SUPABASE_SERVICE_KEY`
     - `QUOTES_TABLE`
     - `TRANSFERS_TABLE`

### 3. **Updated Services**
   - **File**: `app/services/transfer.py`
     - Imports now use `supabase_client` instead of `AppwriteService`
     - Updated `store_transfer_request()` to use Supabase table/data structure
     - Updated `update_transfer_response()` to use Supabase
     - Updated duplicate checking to use Supabase queries
     - Changed field references from `$id` to `id`, `$createdAt` to `created_at`

   - **File**: `app/services/quote.py`
     - Imports now use `supabase_client` instead of `AppwriteService`
     - Updated `store_quote_request()` to use Supabase JSONB for vehicles
     - Updated `update_quote_response()` to use Supabase
     - Updated `get_quote_by_id()` to use Supabase
     - Removed `find_quote_by_phone()` (not currently used)
     - Changed field names to snake_case (e.g., `internalReference` → `internal_reference`)

### 4. **Updated API Endpoints**
   - **File**: `app/api/v1/endpoints/transfer.py`
     - Updated to handle Supabase integer IDs instead of string UUIDs
     - Changed field references from Appwrite format to Supabase format
     - Functions no longer need `await` for database operations

   - **File**: `app/api/v1/endpoints/quote.py`
     - Updated to handle Supabase integer IDs
     - Fixed vehicle data handling (JSONB instead of JSON strings)
     - Updated field mapping for snake_case names
     - Functions no longer need `await` for database operations

### 5. **Environment Configuration**
   - **Development** (`.env`):
     ```bash
     ENVIRONMENT=test
     DEBUG=True
     DEBUG_MODE=True
     SUPABASE_URL=https://supa.usa-solarenergy.com
     SUPABASE_SERVICE_KEY=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJzdXBhYmFzZSIsImlhdCI6MTc1ODgwNjY0MCwiZXhwIjo0OTE0NDgwMjQwLCJyb2xlIjoic2VydmljZV9yb2xlIn0.t76_G_hJiRJnBh35h2QWOJ-geaBQGJyw3LWieOHCEuQ
     QUOTES_TABLE=quotes
     TRANSFERS_TABLE=leads
     ```

   - **Production** (`.env.prod`):
     - Same Supabase configuration
     - `ENVIRONMENT=production`
     - `DEBUG=False`

### 6. **Database Schema**
   - Created `supabase_setup.sql` with:
     - `leads` table (for transfers)
     - `quotes` table (for quote requests)
     - Proper indexes on key fields
     - Row Level Security (RLS) policies
     - Auto-updating `updated_at` triggers

### 7. **Field Name Mapping**

#### Quotes Table
| Old (Appwrite) | New (Supabase) |
|----------------|----------------|
| `$id` | `id` |
| `$createdAt` | `created_at` |
| `$updatedAt` | `updated_at` |
| `internalReference` | `internal_reference` |
| `agentEmail` | `agent_email` |
| `agentBranch` | `agent_branch` |
| `quoteId` | `quote_id` |
| `vehicles` (JSON strings) | `vehicles` (JSONB) |

#### Leads Table
| Old (Appwrite) | New (Supabase) |
|----------------|----------------|
| `$id` | `id` |
| `$createdAt` | `created_at` |
| `$updatedAt` | `updated_at` |
| (all other fields same) | (all other fields same) |

## Next Steps

### 1. Install Dependencies
```bash
pip3 install websockets>=11
pip3 install supabase==2.8.1
```

### 2. Run SQL Setup
1. Log into Supabase dashboard: https://supa.usa-solarenergy.com
2. Go to SQL Editor
3. Copy and paste contents of `supabase_setup.sql`
4. Execute the script
5. Verify tables are created

### 3. Test the API
```bash
# Start the API server
python run.py

# Test in another terminal:
# Test quote endpoint
curl -X POST http://localhost:4000/api/v1/quote \
  -H "Content-Type: application/json" \
  -d '{
    "source": "SureStrat",
    "externalReferenceId": "TEST-001",
    "vehicles": [{
      "make": "Toyota",
      "model": "Corolla",
      "year": 2020,
      "value": 250000
    }],
    "agentEmail": "test@surestrat.co.za",
    "agentBranch": "Test Branch"
  }'

# Test transfer endpoint
curl -X POST http://localhost:4000/api/v1/transfer \
  -H "Content-Type: application/json" \
  -d '{
    "customer_info": {
      "first_name": "Test",
      "last_name": "User",
      "email": "test@example.com",
      "contact_number": "0821234567",
      "id_number": "9001015009087",
      "quote_id": "TEST-001"
    },
    "agent_info": {
      "agent_email": "agent@surestrat.co.za",
      "branch_name": "Test Branch"
    }
  }'
```

### 4. Verify in Supabase Dashboard
- Go to Table Editor
- Check `quotes` table for new records
- Check `leads` table for new records
- Verify data is being stored correctly

## Key Benefits

✅ **Better Performance**: PostgreSQL is faster for complex queries
✅ **JSONB Support**: Native JSON querying with indexes
✅ **Standard SQL**: Familiar syntax and powerful capabilities
✅ **Auto Timestamps**: Triggers handle `updated_at` automatically
✅ **Better Indexing**: Improved query performance
✅ **Duplicate Prevention**: Built-in with proper indexes

## Troubleshooting

### API Won't Start
- Check that `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are set correctly
- Verify Supabase tables exist
- Check logs for detailed error messages

### Database Connection Issues
- Verify Supabase service is running
- Check network connectivity
- Ensure service key has proper permissions

### Duplicate Detection Not Working
- Verify indexes are created on `id_number` and `contact_number`
- Check `check_duplicate_transfer()` function logs
- Ensure data normalization is working

## Documentation
- 📖 **Migration Guide**: See `SUPABASE_MIGRATION.md`
- 📝 **SQL Setup**: See `supabase_setup.sql`
- 🔧 **Configuration**: See `.env` and `.env.prod`

---

**Status**: ✅ Migration Complete
**Environment**: 🧪 Test (Development)
**Next**: Install dependencies and run SQL setup
