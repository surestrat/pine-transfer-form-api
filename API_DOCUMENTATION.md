# Pineapple Surestrat API Documentation

## Table of Contents
- [Overview](#overview)
- [Response Format](#response-format)
- [Error Handling](#error-handling)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Health Check](#health-check)
  - [Quote API](#quote-api)
  - [Transfer API](#transfer-api)
- [Error Codes Reference](#error-codes-reference)
- [Frontend Integration Examples](#frontend-integration-examples)
- [Testing](#testing)

## Overview

The Pineapple Surestrat API provides quote requests and lead transfer functionality between Surestrat and Pineapple Insurance. The API uses FastAPI and returns structured JSON responses with consistent error handling.

**Base URL:** `https://your-api-domain.com`  
**Version:** v1  
**Content-Type:** `application/json`

## Response Format

All API responses follow a consistent structure to make frontend integration predictable and reliable.

### Success Response Structure
```json
{
  "success": true,
  "data": {
    // Actual response data here
  },
  "timestamp": "2025-09-03T14:10:11.123456Z"
}
```

### Error Response Structure
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "User-friendly error message for display",
    "technical_message": "Detailed technical error for debugging",
    "details": {
      // Additional error context
    }
  },
  "timestamp": "2025-09-03T14:10:11.123456Z"
}
```

## Error Handling

### HTTP Status Codes
- `200` - Success
- `201` - Created (for POST requests)
- `400` - Bad Request (validation errors)
- `409` - Conflict (duplicates)
- `500` - Internal Server Error
- `502` - Bad Gateway (external service errors)

### Error Categories

#### Validation Errors (400)
When request data is invalid or missing required fields.

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Please check the provided data and try again.",
    "technical_message": "Request validation failed",
    "details": {
      "validation_errors": [
        {
          "field": "vehicles -> 0 -> make",
          "message": "Field required",
          "input": null,
          "type": "missing"
        }
      ]
    }
  }
}
```

#### Duplicate Errors (409)
When a transfer already exists for the same person.

```json
{
  "success": false,
  "error": {
    "code": "TRANSFER_DUPLICATE",
    "message": "This person has already submitted a transfer request on September 01, 2025 at 14:30 UTC.",
    "technical_message": "Transfer already exists for this ID number (source: database)",
    "details": {
      "submission_date": "2025-09-01T14:30:00Z",
      "transfer_id": "abc123",
      "matched_field": "ID number",
      "source": "database"
    }
  }
}
```

#### External Service Errors (502)
When Pineapple API or other external services fail.

```json
{
  "success": false,
  "error": {
    "code": "QUOTE_API_ERROR",
    "message": "Unable to process your quote request. Please try again later.",
    "technical_message": "Pineapple API error: Invalid vehicle data",
    "details": {}
  }
}
```

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible with CORS enabled for approved domains.

**Allowed Origins:**
- `https://surestrat.co.za`
- `https://webform.surestrat.xyz`
- `https://webform2.surestrat.xyz`
- `http://localhost:5173` (development)
- `http://localhost:4173` (development)
- `http://localhost:3000` (development)
- `http://localhost:4000` (development)

## Endpoints

### Health Check

#### GET `/`
Basic health check endpoint.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "ok",
    "cors_enabled": true
  },
  "timestamp": "2025-09-03T14:10:11.123456Z"
}
```

#### GET `/health`
Detailed health check endpoint.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "cors_enabled": true
  },
  "timestamp": "2025-09-03T14:10:11.123456Z"
}
```

#### GET `/debug/cors`
Debug endpoint to check CORS configuration.

**Response:**
```json
{
  "success": true,
  "data": {
    "allowed_origins_raw": "https://surestrat.co.za,https://webform.surestrat.xyz",
    "allowed_origins_parsed": ["https://surestrat.co.za", "https://webform.surestrat.xyz"],
    "api_environment": "test",
    "is_production": false
  },
  "timestamp": "2025-09-03T14:10:11.123456Z"
}
```

### Quote API

#### POST `/api/v1/quote`
Request a quote from Pineapple Insurance.

**Request Body:**
```json
{
  "source": "SureStrat",
  "externalReferenceId": "QUOTE-1725369011123-456",
  "agentEmail": "agent@surestrat.co.za",
  "agentBranch": "Cape Town",
  "vehicles": [
    {
      "make": "Toyota",
      "model": "Corolla",
      "year": 2020,
      "value": 250000,
      "engine_size": "1.6",
      "fuel_type": "Petrol",
      "transmission": "Manual",
      "vehicle_type": "Car"
    }
  ]
}
```

**Required Fields:**
- `source` - Always "SureStrat"
- `vehicles` - Array of vehicle objects (minimum 1)
- `vehicles[].make` - Vehicle manufacturer
- `vehicles[].model` - Vehicle model
- `vehicles[].year` - Manufacturing year
- `vehicles[].value` - Vehicle value in ZAR

**Optional Fields:**
- `externalReferenceId` - Unique reference ID (auto-generated if not provided)
- `agentEmail` - Agent's email for notifications
- `agentBranch` - Agent's branch name
- `vehicles[].engine_size` - Engine size
- `vehicles[].fuel_type` - Fuel type
- `vehicles[].transmission` - Transmission type
- `vehicles[].vehicle_type` - Type of vehicle

**Success Response (201):**
```json
{
  "success": true,
  "data": {
    "premium": 1240.45,
    "excess": 6200.0,
    "quoteId": "679765d8cdfba62ff342d2ef"
  },
  "timestamp": "2025-09-03T14:10:11.123456Z"
}
```

**Error Responses:**

**Validation Error (400):**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Please check the provided data and try again.",
    "technical_message": "Request validation failed",
    "details": {
      "validation_errors": [
        {
          "field": "vehicles",
          "message": "Field required",
          "input": null,
          "type": "missing"
        }
      ]
    }
  }
}
```

**Storage Error (500):**
```json
{
  "success": false,
  "error": {
    "code": "QUOTE_STORAGE_ERROR",
    "message": "Unable to save your quote request. Please try again.",
    "technical_message": "Database error: Connection timeout",
    "details": {}
  }
}
```

**API Error (502):**
```json
{
  "success": false,
  "error": {
    "code": "QUOTE_API_ERROR",
    "message": "Unable to process your quote request. Please try again later.",
    "technical_message": "Pineapple API error: Invalid vehicle data",
    "details": {}
  }
}
```

### Transfer API

#### POST `/api/v1/transfer`
Transfer a lead to Pineapple Insurance.

**Request Body:**
```json
{
  "customer_info": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "contact_number": "0821234567",
    "id_number": "8001015009080",
    "quote_id": "QUOTE-1725369011123-456"
  },
  "agent_info": {
    "agent_email": "agent@surestrat.co.za",
    "branch_name": "Cape Town"
  }
}
```

**Required Fields:**
- `customer_info.first_name` - Customer's first name
- `customer_info.last_name` - Customer's last name
- `customer_info.email` - Customer's email address
- `customer_info.contact_number` - Customer's phone number
- `customer_info.id_number` - Customer's ID number
- `agent_info.agent_email` - Agent's email address
- `agent_info.branch_name` - Agent's branch name

**Optional Fields:**
- `customer_info.quote_id` - Reference to quote ID

**Success Response (201):**
```json
{
  "success": true,
  "data": {
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "redirect_url": "https://pineapple.co.za/quote/550e8400-e29b-41d4-a716-446655440000"
  },
  "timestamp": "2025-09-03T14:10:11.123456Z"
}
```

**Error Responses:**

**Duplicate Transfer (409):**
```json
{
  "success": false,
  "error": {
    "code": "TRANSFER_DUPLICATE",
    "message": "This person has already submitted a transfer request on September 01, 2025 at 14:30 UTC.",
    "technical_message": "Transfer already exists for this ID number (source: database)",
    "details": {
      "submission_date": "2025-09-01T14:30:00Z",
      "transfer_id": "abc123",
      "matched_field": "ID number",
      "source": "database"
    }
  }
}
```

**Validation Error (400):**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Please check the provided data and try again.",
    "technical_message": "Request validation failed",
    "details": {
      "validation_errors": [
        {
          "field": "customer_info -> email",
          "message": "Field required",
          "input": null,
          "type": "missing"
        }
      ]
    }
  }
}
```

**Storage Error (500):**
```json
{
  "success": false,
  "error": {
    "code": "TRANSFER_STORAGE_ERROR",
    "message": "Unable to save your transfer request. Please try again.",
    "technical_message": "Database error: Connection timeout",
    "details": {}
  }
}
```

**API Error (502):**
```json
{
  "success": false,
  "error": {
    "code": "TRANSFER_API_ERROR",
    "message": "Unable to process your transfer request. Please try again later.",
    "technical_message": "Pineapple API error: Invalid customer data",
    "details": {}
  }
}
```

## Error Codes Reference

### Quote Errors
| Code | Status | Description | User Action |
|------|--------|-------------|-------------|
| `QUOTE_VALIDATION_ERROR` | 400 | Invalid quote data | Check form data and retry |
| `QUOTE_STORAGE_ERROR` | 500 | Database error | Retry request |
| `QUOTE_API_ERROR` | 502 | Pineapple API error | Retry later |
| `QUOTE_RESPONSE_ERROR` | 502 | Invalid API response | Retry later |

### Transfer Errors
| Code | Status | Description | User Action |
|------|--------|-------------|-------------|
| `TRANSFER_VALIDATION_ERROR` | 400 | Invalid transfer data | Check form data and retry |
| `TRANSFER_DUPLICATE` | 409 | Transfer already exists | Show existing transfer info |
| `TRANSFER_STORAGE_ERROR` | 500 | Database error | Retry request |
| `TRANSFER_API_ERROR` | 502 | Pineapple API error | Retry later |
| `TRANSFER_RESPONSE_ERROR` | 502 | Invalid API response | Retry later |

### General Errors
| Code | Status | Description | User Action |
|------|--------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed | Fix validation errors |
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected server error | Retry later |
| `DATABASE_ERROR` | 500 | Database connection error | Retry later |
| `EXTERNAL_SERVICE_ERROR` | 502 | External service error | Retry later |
| `EMAIL_ERROR` | 500 | Email sending failed | Request completed but no notification |

## Frontend Integration Examples

### React/JavaScript Example

```javascript
class PineappleAPI {
  constructor(baseUrl = 'https://your-api-domain.com') {
    this.baseUrl = baseUrl;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (data.success) {
        return { success: true, data: data.data };
      } else {
        return { success: false, error: data.error };
      }
    } catch (error) {
      return {
        success: false,
        error: {
          code: 'NETWORK_ERROR',
          message: 'Network error occurred. Please check your connection.',
          technical_message: error.message,
          details: {}
        }
      };
    }
  }

  async getQuote(quoteData) {
    return this.request('/api/v1/quote', {
      method: 'POST',
      body: JSON.stringify(quoteData),
    });
  }

  async transferLead(transferData) {
    return this.request('/api/v1/transfer', {
      method: 'POST',
      body: JSON.stringify(transferData),
    });
  }
}

// Usage Example
const api = new PineappleAPI();

// Quote request
async function handleQuoteSubmit(formData) {
  const quoteData = {
    source: "SureStrat",
    externalReferenceId: `QUOTE-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
    agentEmail: formData.agentEmail,
    agentBranch: formData.agentBranch,
    vehicles: formData.vehicles
  };

  const result = await api.getQuote(quoteData);

  if (result.success) {
    // Handle successful quote
    const { premium, excess, quoteId } = result.data;
    showQuoteResult(premium, excess, quoteId);
  } else {
    // Handle errors
    handleError(result.error);
  }
}

// Transfer request
async function handleTransferSubmit(formData) {
  const transferData = {
    customer_info: {
      first_name: formData.firstName,
      last_name: formData.lastName,
      email: formData.email,
      contact_number: formData.phone,
      id_number: formData.idNumber,
      quote_id: formData.quoteId
    },
    agent_info: {
      agent_email: formData.agentEmail,
      branch_name: formData.branchName
    }
  };

  const result = await api.transferLead(transferData);

  if (result.success) {
    // Handle successful transfer
    const { uuid, redirect_url } = result.data;
    redirectToQuote(redirect_url);
  } else {
    // Handle errors
    handleError(result.error);
  }
}

// Error handling function
function handleError(error) {
  switch (error.code) {
    case 'VALIDATION_ERROR':
      showValidationErrors(error.details.validation_errors);
      break;

    case 'TRANSFER_DUPLICATE':
      const { submission_date, matched_field, source } = error.details;
      showDuplicateError(
        `This ${matched_field.toLowerCase()} was already submitted on ${new Date(submission_date).toLocaleDateString()}.`,
        source === 'pineapple' ? 'This lead is still active in Pineapple system (within 90 days).' : ''
      );
      break;

    case 'QUOTE_API_ERROR':
    case 'TRANSFER_API_ERROR':
      showTemporaryError(error.message, 'Please try again in a few minutes.');
      break;

    case 'QUOTE_STORAGE_ERROR':
    case 'TRANSFER_STORAGE_ERROR':
      showRetryableError(error.message, 'Please try submitting again.');
      break;

    case 'NETWORK_ERROR':
      showNetworkError('Please check your internet connection and try again.');
      break;

    default:
      showGenericError(error.message || 'An unexpected error occurred.');
  }
}

// UI Helper Functions
function showQuoteResult(premium, excess, quoteId) {
  // Display quote results to user
  document.getElementById('premium').textContent = `R${premium.toFixed(2)}`;
  document.getElementById('excess').textContent = `R${excess.toFixed(2)}`;
  document.getElementById('quote-id').textContent = quoteId;
}

function showValidationErrors(validationErrors) {
  validationErrors.forEach(error => {
    const field = error.field.split(' -> ').pop(); // Get the field name
    const fieldElement = document.getElementById(field);
    if (fieldElement) {
      fieldElement.classList.add('error');
      // Show error message near the field
      const errorElement = document.createElement('div');
      errorElement.className = 'error-message';
      errorElement.textContent = error.message;
      fieldElement.parentNode.appendChild(errorElement);
    }
  });
}

function showDuplicateError(message, additionalInfo = '') {
  const errorDiv = document.getElementById('error-message');
  errorDiv.innerHTML = `
    <div class="error duplicate-error">
      <h4>Duplicate Submission</h4>
      <p>${message}</p>
      ${additionalInfo ? `<p><small>${additionalInfo}</small></p>` : ''}
    </div>
  `;
}

function showTemporaryError(message, suggestion) {
  const errorDiv = document.getElementById('error-message');
  errorDiv.innerHTML = `
    <div class="error temporary-error">
      <h4>Service Temporarily Unavailable</h4>
      <p>${message}</p>
      <p><small>${suggestion}</small></p>
    </div>
  `;
}

function showRetryableError(message, suggestion) {
  const errorDiv = document.getElementById('error-message');
  errorDiv.innerHTML = `
    <div class="error retryable-error">
      <h4>Request Failed</h4>
      <p>${message}</p>
      <p><small>${suggestion}</small></p>
      <button onclick="retryLastRequest()">Retry</button>
    </div>
  `;
}

function showNetworkError(message) {
  const errorDiv = document.getElementById('error-message');
  errorDiv.innerHTML = `
    <div class="error network-error">
      <h4>Connection Error</h4>
      <p>${message}</p>
    </div>
  `;
}

function showGenericError(message) {
  const errorDiv = document.getElementById('error-message');
  errorDiv.innerHTML = `
    <div class="error generic-error">
      <h4>Error</h4>
      <p>${message}</p>
    </div>
  `;
}

function redirectToQuote(url) {
  // Redirect user to Pineapple quote page
  window.location.href = url;
}
```

### TypeScript Interfaces

```typescript
// API Response Types
interface APIResponse<T> {
  success: boolean;
  data?: T;
  error?: APIError;
  timestamp: string;
}

interface APIError {
  code: string;
  message: string;
  technical_message: string;
  details: Record<string, any>;
}

// Quote Types
interface QuoteRequest {
  source: "SureStrat";
  externalReferenceId?: string;
  agentEmail?: string;
  agentBranch?: string;
  vehicles: Vehicle[];
}

interface Vehicle {
  make: string;
  model: string;
  year: number;
  value: number;
  engine_size?: string;
  fuel_type?: string;
  transmission?: string;
  vehicle_type?: string;
}

interface QuoteResponse {
  premium: number;
  excess: number;
  quoteId: string;
}

// Transfer Types
interface TransferRequest {
  customer_info: CustomerInfo;
  agent_info: AgentInfo;
}

interface CustomerInfo {
  first_name: string;
  last_name: string;
  email: string;
  contact_number: string;
  id_number: string;
  quote_id?: string;
}

interface AgentInfo {
  agent_email: string;
  branch_name: string;
}

interface TransferResponse {
  uuid: string;
  redirect_url: string;
}

// Validation Error Types
interface ValidationError {
  field: string;
  message: string;
  input: any;
  type: string;
}

// Duplicate Error Details
interface DuplicateErrorDetails {
  submission_date: string;
  transfer_id: string;
  matched_field: string;
  source: 'database' | 'pineapple';
}
```

## Testing

### Manual Testing with cURL

**Health Check:**
```bash
curl -X GET "https://your-api-domain.com/health"
```

**Quote Request:**
```bash
curl -X POST "https://your-api-domain.com/api/v1/quote" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "SureStrat",
    "externalReferenceId": "TEST-QUOTE-123",
    "vehicles": [
      {
        "make": "Toyota",
        "model": "Corolla",
        "year": 2020,
        "value": 250000
      }
    ]
  }'
```

**Transfer Request:**
```bash
curl -X POST "https://your-api-domain.com/api/v1/transfer" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_info": {
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@example.com",
      "contact_number": "0821234567",
      "id_number": "8001015009080"
    },
    "agent_info": {
      "agent_email": "agent@surestrat.co.za",
      "branch_name": "Cape Town"
    }
  }'
```

### Postman Collection

You can import this collection into Postman for testing:

```json
{
  "info": {
    "name": "Pineapple Surestrat API",
    "description": "API for quote requests and lead transfers"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{baseUrl}}/health",
          "host": ["{{baseUrl}}"],
          "path": ["health"]
        }
      }
    },
    {
      "name": "Quote Request",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"source\": \"SureStrat\",\n  \"externalReferenceId\": \"TEST-QUOTE-123\",\n  \"vehicles\": [\n    {\n      \"make\": \"Toyota\",\n      \"model\": \"Corolla\",\n      \"year\": 2020,\n      \"value\": 250000\n    }\n  ]\n}"
        },
        "url": {
          "raw": "{{baseUrl}}/api/v1/quote",
          "host": ["{{baseUrl}}"],
          "path": ["api", "v1", "quote"]
        }
      }
    },
    {
      "name": "Transfer Request",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"customer_info\": {\n    \"first_name\": \"John\",\n    \"last_name\": \"Doe\",\n    \"email\": \"john.doe@example.com\",\n    \"contact_number\": \"0821234567\",\n    \"id_number\": \"8001015009080\"\n  },\n  \"agent_info\": {\n    \"agent_email\": \"agent@surestrat.co.za\",\n    \"branch_name\": \"Cape Town\"\n  }\n}"
        },
        "url": {
          "raw": "{{baseUrl}}/api/v1/transfer",
          "host": ["{{baseUrl}}"],
          "path": ["api", "v1", "transfer"]
        }
      }
    }
  ],
  "variable": [
    {
      "key": "baseUrl",
      "value": "https://your-api-domain.com"
    }
  ]
}
```

## Best Practices

### Frontend Best Practices

1. **Always check the `success` field** before processing data
2. **Handle all error codes** with appropriate user messages
3. **Show validation errors** near the relevant form fields
4. **Implement retry logic** for temporary errors
5. **Log technical messages** for debugging (don't show to users)
6. **Provide clear feedback** for duplicate submissions
7. **Handle network errors** gracefully

### Error Handling Best Practices

1. **Never show technical messages** to end users
2. **Provide actionable guidance** in error messages
3. **Differentiate between retryable and non-retryable errors**
4. **Log full error context** for debugging
5. **Implement exponential backoff** for retries
6. **Cache successful responses** to avoid duplicate requests

### Security Considerations

1. **Validate all input** on the frontend before sending
2. **Never trust error messages** for sensitive information
3. **Implement rate limiting** on your frontend
4. **Log security-relevant errors** for monitoring
5. **Use HTTPS** for all requests

## Support

For technical support or questions about this API, contact the development team or refer to the internal documentation.

**Last Updated:** September 3, 2025  
**API Version:** v1  
**Documentation Version:** 1.0
