# SureStrat API - Frontend Integration Guide

This document provides information about how to integrate with the SureStrat API from a frontend application. It includes data requirements and axios examples for both quote and lead transfer endpoints.

## API Endpoints

The API provides two main endpoints:

1. `/api/v1/quote` - For requesting insurance quotes
2. `/api/v1/transfer` - For transferring lead information to Pineapple

## Quote Request

### Required Data Structure

The quote request endpoint requires a structured JSON payload with the following format:

```json
{
  "source": "SureStrat",
  "externalReferenceId": "YOUR_UNIQUE_REFERENCE",
  "agentEmail": "agent@example.com",
  "agentBranch": "Sandton Branch",
  "vehicles": [
    {
      "year": 2022,
      "make": "Toyota",
      "model": "Corolla",
      "mmCode": "TOYC2022",
      "modified": "No",
      "category": "Sedan",
      "colour": "White",
      "engineSize": 1.8,
      "financed": "Yes",
      "owner": "Self",
      "status": "New",
      "partyIsRegularDriver": "Yes",
      "accessories": "None",
      "accessoriesAmount": 0,
      "retailValue": 450000,
      "marketValue": 430000,
      "insuredValueType": "Retail",
      "useType": "Private",
      "overnightParkingSituation": "Lock-up Garage",
      "coverCode": "Comprehensive",
      "address": {
        "addressLine": "123 Main Street",
        "postalCode": 2000,
        "suburb": "Sandton",
        "latitude": -26.107567,
        "longitude": 28.056702
      },
      "regularDriver": {
        "maritalStatus": "Married",
        "currentlyInsured": true,
        "yearsWithoutClaims": 5,
        "relationToPolicyHolder": "Self",
        "emailAddress": "customer@example.com",
        "mobileNumber": "0821234567",
        "idNumber": "8001015009087",
        "licenseIssueDate": "2010-01-15",
        "dateOfBirth": "1980-01-01"
      }
    }
  ]
}
```

**Note**: For quotes, use `agentEmail` and `agentBranch` (camelCase). For transfers, use `agent_email` and `branch_name` (snake_case).

### Response Structure

```json
{
  "premium": 1250.75,
  "excess": 3500.00
}
```

### Axios Example - Quote Request

```javascript
import axios from 'axios';

const requestQuote = async (quoteData) => {
  try {
    // Generate a unique reference ID
    const uniqueRef = `QUOTE-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
    
    // Ensure source is properly set
    const payload = {
      ...quoteData,
      source: "SureStrat",
      externalReferenceId: uniqueRef,
      agentEmail: quoteData.agentEmail || "default@agent.com",
      agentBranch: quoteData.agentBranch || "Default Branch"
    };
    
    const response = await axios.post('https://your-api-domain.com/api/v1/quote', payload, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    return {
      success: true,
      data: response.data,
      referenceId: uniqueRef
    };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to get quote',
      status: error.response?.status
    };
  }
};
```

## Lead Transfer

### Required Data Structure

```json
{
  "customer_info": {
    "first_name": "John",
    "last_name": "Smith",
    "email": "john.smith@example.com",
    "contact_number": "0821234567",
    "id_number": "8001015009087",
    "quote_id": "QUOTE-12345"
  },
  "agent_info": {
    "agent_email": "john.doe@surestrat.co.za",
    "branch_name": "Sandton Branch"
  }
}
```

**Note**: For transfers, use `agent_email` and `branch_name` (snake_case). For quotes, use `agentEmail` and `agentBranch` (camelCase).

### Response Structure

```json
{
  "uuid": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "redirect_url": "https://portal.pineapple.co.za/quote/a1b2c3d4-e5f6"
}
```

### Duplicate Prevention

The API automatically prevents duplicate lead transfers by checking both ID number and contact number. If a duplicate is found, the API returns an HTTP 409 Conflict response with details about the existing transfer.

#### Duplicate Check Behavior
- **Primary Check**: ID number (if provided)
- **Secondary Check**: Contact number (if ID number check fails)
- **Normalization**: Spaces, dashes, and plus signs are automatically removed for consistent matching
- **Response**: Includes the submission date and which field matched

#### Example Duplicate Error Response

```json
{
  "detail": "Transfer already exists for this ID number. Existing transfer ID: abc123def, submitted on: 2025-09-01 14:30:25 UTC"
}
```

or

```json
{
  "detail": "Transfer already exists for this contact number. Existing transfer ID: xyz789ghi, submitted on: 2025-08-15 09:15:42 UTC"
}
```

### Axios Example - Lead Transfer

```javascript
import axios from 'axios';

const transferLead = async (customerData, agentData, quoteId) => {
  try {
    const payload = {
      customer_info: {
        ...customerData,
        quote_id: quoteId
      },
      agent_info: {
        agent_email: agentData.agentEmail || agentData.agent_email,
        branch_name: agentData.agentBranch || agentData.branch_name
      }
    };
    
    const response = await axios.post('https://your-api-domain.com/api/v1/transfer', payload, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    return {
      success: true,
      data: response.data
    };
  } catch (error) {
    // Handle different error types
    if (error.response?.status === 409) {
      // Duplicate transfer detected
      return {
        success: false,
        error: error.response.data.detail,
        type: 'duplicate',
        status: 409
      };
    } else if (error.response?.status === 400) {
      // Bad request - validation error
      return {
        success: false,
        error: error.response.data.detail || 'Invalid request data',
        type: 'validation',
        status: 400
      };
    } else if (error.response?.status === 502) {
      // Pineapple API error
      return {
        success: false,
        error: 'Unable to process transfer at this time. Please try again later.',
        type: 'external_api',
        status: 502
      };
    } else {
      // Other errors
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to transfer lead',
        status: error.response?.status || 500
      };
    }
  }
};
```

## Common Integration Example

Below is a more complete example showing how you might integrate both quote and transfer functionality in a React component:

```jsx
import React, { useState } from 'react';
import axios from 'axios';

const API_BASE_URL = 'https://api.surestrat.co.za';

const InsuranceForm = () => {
  const [quoteData, setQuoteData] = useState(null);
  const [quoteId, setQuoteId] = useState(null);
  const [transferData, setTransferData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Step 1: Request a quote
  const handleQuoteRequest = async (formData) => {
    setLoading(true);
    setError(null);
    
    try {
      // Transform form data to match API requirements
      const quotePayload = {
        source: "SureStrat",
        externalReferenceId: `QUOTE-${Date.now()}`,
        agentEmail: formData.agentEmail || "website@example.com",
        agentBranch: formData.agentBranch || "Online Branch",
        vehicles: [
          {
            year: formData.vehicleYear,
            make: formData.vehicleMake,
            model: formData.vehicleModel,
            retailValue: formData.vehicleValue,
            // Add other required vehicle fields...
            
            address: {
              addressLine: formData.address,
              postalCode: formData.postalCode,
              suburb: formData.suburb
            },
            
            regularDriver: {
              maritalStatus: formData.maritalStatus,
              currentlyInsured: formData.currentlyInsured,
              yearsWithoutClaims: formData.claimFreeYears,
              relationToPolicyHolder: "Self",
              emailAddress: formData.email,
              mobileNumber: formData.phone,
              idNumber: formData.idNumber
            }
          }
        ]
      };
      
      const response = await axios.post(`${API_BASE_URL}/api/v1/quote`, quotePayload);
      
      setQuoteData(response.data);
      setQuoteId(quotePayload.externalReferenceId);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to get quote');
      console.error('Quote error:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Step 2: Transfer lead if customer accepts the quote
  const handleLeadTransfer = async (customerInfo) => {
    setLoading(true);
    setError(null);
    
    try {
      const transferPayload = {
        customer_info: {
          first_name: customerInfo.firstName,
          last_name: customerInfo.lastName,
          email: customerInfo.email,
          contact_number: customerInfo.phone,
          id_number: customerInfo.idNumber,
          quote_id: quoteId
        },
        agent_info: {
          agent_email: customerInfo.agentEmail || "website@example.com",
          branch_name: customerInfo.agentBranch || "Online Branch"
        }
      };
      
      const response = await axios.post(`${API_BASE_URL}/api/v1/transfer`, transferPayload);
      
      setTransferData(response.data);
      
      // Redirect to Pineapple if a redirect URL is provided
      if (response.data.redirect_url) {
        window.location.href = response.data.redirect_url;
      }
    } catch (err) {
      if (err.response?.status === 409) {
        // Handle duplicate transfer
        setError(`This customer has already been transferred. ${err.response.data.detail}`);
      } else if (err.response?.status === 400) {
        // Handle validation errors
        setError(`Please check your information: ${err.response.data.detail}`);
      } else if (err.response?.status === 502) {
        // Handle external API errors
        setError('Unable to process transfer at this time. Please try again later.');
      } else {
        // Handle other errors
        setError(err.response?.data?.detail || 'Failed to transfer lead');
      }
      console.error('Transfer error:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Render form components and handlers
  return (
    <div>
      {/* Form components go here */}
    </div>
  );
};

export default InsuranceForm;
```

## Agent Information Fields

### Important: Field Naming Conventions

The API uses different field naming conventions for agent information depending on the endpoint:

#### For Quote Requests (`/api/v1/quote`)
Use **camelCase** field names:
```json
{
  "agentEmail": "agent@example.com",
  "agentBranch": "Sandton Branch"
}
```

#### For Transfer Requests (`/api/v1/transfer`)
Use **snake_case** field names:
```json
{
  "agent_email": "agent@example.com",
  "branch_name": "Sandton Branch"
}
```

### Agent Field Requirements

- **agentEmail/agent_email**: Required for both endpoints
- **agentBranch/branch_name**: Required for both endpoints
- Both fields are used for tracking and reporting purposes
- The API will store this information with the request for audit trails

## Important Notes

1. Always validate user input before sending to the API
2. Handle errors gracefully and provide clear feedback to users
3. Store the `externalReferenceId` from the quote request, as it's needed for the transfer
4. Email addresses must be valid format
5. Phone numbers should be in the format '0821234567' (no spaces or special characters)

## Handling Duplicate Transfers

When a duplicate transfer is detected (HTTP 409), consider these user experience best practices:

### User Feedback
- **Clear Message**: Show the exact error message from the API, which includes when the original transfer was submitted
- **Actionable Options**: Provide options like "Contact Support" or "View Existing Transfer"
- **Prevention**: Consider pre-checking for duplicates before submission using a separate validation endpoint

### Example Duplicate Handling

```javascript
// Handle duplicate transfer in your UI
const handleDuplicateTransfer = (errorDetail) => {
  // Parse the error message to extract useful information
  const match = errorDetail.match(/submitted on: ([^)]+)/);
  const submissionDate = match ? match[1] : 'unknown date';
  
  // Show user-friendly message
  showNotification({
    type: 'warning',
    title: 'Transfer Already Exists',
    message: `This customer was already transferred on ${submissionDate}. Please check with the customer or contact support if you need to make changes.`,
    actions: [
      {
        label: 'Contact Support',
        action: () => openSupportChat()
      }
    ]
  });
};
```

### Prevention Strategies
- **Pre-submission Check**: Implement a "Check for Existing Transfer" button before the main submit
- **Form Validation**: Highlight ID number and contact number fields as key duplicate prevention fields
- **User Confirmation**: For high-value transfers, ask for confirmation when these fields match existing records

## Data Input Guidelines

### Field Normalization
The API automatically normalizes certain fields for duplicate detection:
- **ID Numbers**: Spaces and dashes are removed (e.g., "80 0101 5009 087" → "8001015009087")
- **Contact Numbers**: Spaces, dashes, and plus signs are removed (e.g., "+27 82 123 4567" → "27821234567")

### Best Practices for Input
- **ID Numbers**: Accept various formats but consider normalizing on the frontend for consistency
- **Contact Numbers**: Use international format without special characters for best compatibility
- **Required Fields**: Both `id_number` and `contact_number` are required for optimal duplicate prevention

## Response Codes

- `201 Created`: Request processed successfully
- `400 Bad Request`: Invalid input data
- `409 Conflict`: Duplicate transfer detected (includes submission date and details)
- `500 Internal Server Error`: Server-side issue
- `502 Bad Gateway`: Issue communicating with the Pineapple API

For more detailed API information, refer to the API documentation or contact support.
