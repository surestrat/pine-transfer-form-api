# AI Coding Assistant Instructions for Surestrat Pineapple Integration API

## Project Overview
This is a FastAPI-based REST API that integrates Surestrat with Pineapple Insurance, providing quote requests and lead transfer functionality. The system uses Appwrite as its database backend and sends email notifications via SMTP.

## Architecture & Key Components

### Core Structure
- **API Layer**: FastAPI with custom CORS middleware (`main.py`)
- **Endpoints**: `/api/v1/quote` and `/api/v1/transfer` (`app/api/v1/endpoints/`)
- **Services**: Business logic in `app/services/` (quote.py, transfer.py, email.py)
- **Data Models**: Pydantic schemas in `app/schemas/` (quote.py, transfer.py)
- **Database**: Appwrite integration via `app/utils/appwrite.py`
- **Configuration**: Environment-based settings in `config/settings.py`

### Data Flow Patterns

#### Quote Request Flow
1. **Store Request**: Save to Appwrite `quote` collection with JSON-serialized vehicles
2. **Call Pineapple API**: POST to `/api/v1/quote/quick-quote` with "SureStrat" source
3. **Parse Response**: Extract premium/excess from nested Pineapple response structure
4. **Store Response**: Update document with parsed values
5. **Send Notification**: Background email to admins using `quote_notification.html` template

### Transfer Request Flow
1. **Validate Input**: Check for existing transfers by ID number OR contact number to prevent duplicates
2. **Duplicate Prevention**: Return HTTP 409 with submission date if duplicate found
3. **Store Request**: Save to Appwrite `transfer` collection with agent information
4. **Transform Data**: Convert internal format to Pineapple's flat structure
5. **Call Pineapple API**: POST to `/users/motor_lead` endpoint with agent details
6. **Parse Response**: Extract UUID and redirect_url from response
7. **Store Response**: Update document with Pineapple response
8. **Send Notification**: Background email using `transfer_notification.html` template

### Duplicate Prevention
- **Check Fields**: ID number (primary) and contact number (secondary)
- **Normalization**: Remove spaces, dashes, and plus signs from identifiers
- **Response**: HTTP 409 with existing transfer ID and submission date
- **Database Indexes**: Unique constraints on both `id_number` and `contact_number`
- **Logging**: Detailed logs for duplicate attempts with matched field type

## Critical Implementation Patterns

### Source Identification
```python
# Always use "SureStrat" (case-sensitive, not "surestrat")
"source": "SureStrat"
```

### External Reference IDs
```python
# Generate unique reference for tracking across systems
externalReferenceId = f"QUOTE-{Date.now()}-{Math.floor(Math.random() * 1000)}"
```

### Environment Configuration
```python
# Dynamic credential selection based on ENVIRONMENT variable
@property
def PINEAPPLE_API_KEY(self) -> str:
    return self.PINEAPPLE_PROD_API_KEY if self.IS_PRODUCTION else self.PINEAPPLE_TEST_API_KEY
```

### Appwrite Document Storage
```python
# Vehicles stored as JSON strings in Appwrite
"vehicles": json.dumps([vehicle.model_dump(mode="json") for vehicle in quote_data.vehicles])
```

### Error Handling
```python
# Return 502 for Pineapple API errors, not 500
raise HTTPException(status_code=502, detail=f"Pineapple API error: {error_message}")
```

### Background Tasks
```python
# Email notifications sent asynchronously
background_tasks.add_task(email_service.send_email, ...)
```

## Development Workflow

### Local Development Setup
```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file (copy from .env.example)
cp .env.example .env

# 4. Run with auto-reload
python run.py
```

### Docker Development
```bash
# Build and run with docker-compose
docker-compose up -d --build
```

### Key Environment Variables
```bash
# Required for functionality
ENVIRONMENT=test|production
PINEAPPLE_TEST_API_KEY=...
PINEAPPLE_TEST_API_SECRET=...
APPWRITE_ENDPOINT=...
APPWRITE_PROJECT_ID=...
APPWRITE_API_KEY=...
DATABASE_ID=...
QUOTE_COL_ID=...
TRANSFER_COL_ID=...
SMTP_SERVER=...
SMTP_USERNAME=...
SMTP_PASSWORD=...
ADMIN_EMAILS=...
```

## Testing & Debugging

### Common Issues
- **CORS errors**: Check `ALLOWED_ORIGINS` parsing in `main.py`
- **Pineapple API failures**: Verify test/prod credentials and endpoints
- **Email delivery**: Check SMTP configuration and recipient parsing
- **Appwrite connection**: Validate collection IDs and database permissions

### Logging
```python
# Rich logging enabled by default
from app.utils.rich_logger import get_rich_logger
logger = get_rich_logger("component_name")
```

### Health Checks
- `GET /` - Basic health check
- `GET /health` - Detailed health check
- `GET /debug/cors` - CORS configuration debug

## Code Style & Conventions

### Import Organization
```python
# Standard library first
import json
import logging

# Third-party packages
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Local imports
from config.settings import settings
from app.schemas.quote import QuoteRequest
```

### Error Response Format
```python
# Consistent error structure
{"error": "Descriptive error message"}
```

### UUID Generation
```python
# Use custom safe_uuid() for Appwrite document IDs
document_id = safe_uuid()  # Returns 8-char string without hyphens
```

### Data Validation
```python
# Use Pydantic models with extra="allow" for flexibility
model_config = {
    "extra": "allow",
    "validate_assignment": True
}
```

## Integration Points

### Pineapple API
- **Quote Endpoint**: `POST /api/v1/quote/quick-quote`
- **Transfer Endpoint**: `POST /users/motor_lead`
- **Authentication**: `Bearer KEY={api_key} SECRET={secret}`
- **Test Environment**: `http://gw-test.pineapple.co.za`
- **Prod Environment**: `http://gw.pineapple.co.za`

### Appwrite Collections
- **Quote Collection**: Stores quote requests/responses with JSON vehicles
- **Transfer Collection**: Stores lead transfers with agent information
- **Query Pattern**: Use `Query.equal()` for searches (SDK limitation workaround)

### Quote Collection Schema
```javascript
// Required attributes for quotes collection:
{
  "source": "string",           // Always "SureStrat"
  "internalReference": "string", // Unique reference ID (matches Appwrite schema)
  "status": "string",           // "PENDING" initially, updated after response
  "vehicles": "string[]",       // Array of vehicle objects (NOT JSON string)
  "premium": "string",          // Premium amount as string (NOT double)
  "excess": "string",           // Excess amount as string (NOT double)
  "agentEmail": "string",       // Agent's email address (optional)
  "agentBranch": "string"       // Agent's branch name (optional)
}
```

### Transfer Collection Schema  
```javascript
// Required attributes for transfers collection:
{
  "first_name": "string",
  "last_name": "string", 
  "email": "string",
  "contact_number": "string",
  "id_number": "string",
  "quote_id": "string",
  "agent_email": "string",     // PRIMARY: Agent's email address (used in API calls)
  "agent_name": "string",      // LEGACY: Copy of agent_email for backward compatibility
  "branch_name": "string",     // Agent's branch name
  "created_at": "string",      // ISO timestamp
  "updated_at": "string",      // ISO timestamp
  "uuid": "string",            // From Pineapple response
  "redirect_url": "string"     // From Pineapple response
}
```

### Email Templates
- **Location**: `templates/` directory
- **Engine**: Jinja2 with autoescape
- **Context**: Always includes `now` datetime
- **Recipients**: Parsed from comma-separated `ADMIN_EMAILS`

## Deployment Considerations

### Containerization
- **Base Image**: `python:3.12-slim`
- **Port**: 4000 (configurable via `PORT`)
- **Volume Mount**: Source code for development
- **Environment**: All config via environment variables

### Production Checklist
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure production Pineapple credentials
- [ ] Set up production Appwrite instance
- [ ] Configure production SMTP settings
- [ ] Update `ALLOWED_ORIGINS` for production domain
- [ ] Enable production logging level

## File Organization Reference

```
app/
├── api/v1/endpoints/     # FastAPI route handlers
├── schemas/             # Pydantic data models
├── services/            # Business logic layer
└── utils/               # Helper utilities (appwrite, logging)

config/
└── settings.py          # Environment configuration

templates/               # Jinja2 email templates
scripts/                 # Utility scripts (appwrite_schema.py)
```

## Security Notes
- API keys stored as environment variables
- No sensitive data logged (credentials masked in logs)
- CORS configured per environment
- Input validation via Pydantic models
- HTTPS recommended for production
