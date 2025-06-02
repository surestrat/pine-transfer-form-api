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
      externalReferenceId: uniqueRef
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
    "agent_name": "Sarah Jones",
    "branch_name": "Sandton Branch"
  }
}
```

### Response Structure

```json
{
  "uuid": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "redirect_url": "https://portal.pineapple.co.za/quote/a1b2c3d4-e5f6"
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
      agent_info: agentData
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
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to transfer lead',
      status: error.response?.status
    };
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
          agent_name: "Website Lead",
          branch_name: "Online Branch"
        }
      };
      
      const response = await axios.post(`${API_BASE_URL}/api/v1/transfer`, transferPayload);
      
      setTransferData(response.data);
      
      // Redirect to Pineapple if a redirect URL is provided
      if (response.data.redirect_url) {
        window.location.href = response.data.redirect_url;
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to transfer lead');
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

## Important Notes

1. Always validate user input before sending to the API
2. Handle errors gracefully and provide clear feedback to users
3. Store the `externalReferenceId` from the quote request, as it's needed for the transfer
4. Email addresses must be valid format
5. Phone numbers should be in the format '0821234567' (no spaces or special characters)

## Response Codes

- `201 Created`: Request processed successfully
- `400 Bad Request`: Invalid input data
- `500 Internal Server Error`: Server-side issue
- `502 Bad Gateway`: Issue communicating with the Pineapple API

For more detailed API information, refer to the API documentation or contact support.
