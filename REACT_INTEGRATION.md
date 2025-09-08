# React Integration Guide for Pineapple Surestrat API

## Table of Contents
- [Setup](#setup)
- [Custom Hooks](#custom-hooks)
- [API Service](#api-service)
- [Component Examples](#component-examples)
- [Error Handling](#error-handling)
- [State Management](#state-management)
- [Forms and Validation](#forms-and-validation)
- [TypeScript Support](#typescript-support)
- [Best Practices](#best-practices)

## Setup

### Installation
```bash
npm install axios react-hook-form zod @hookform/resolvers
# or
yarn add axios react-hook-form zod @hookform/resolvers
```

### Environment Variables
Create a `.env` file in your React project root:
```env
REACT_APP_API_BASE_URL=https://your-api-domain.com
REACT_APP_API_VERSION=v1
```

### API Service Setup

Create `src/services/pineappleApi.js`:
```javascript
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;
const API_VERSION = process.env.REACT_APP_API_VERSION || 'v1';

// Create axios instance
const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/${API_VERSION}`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Response interceptor to handle the API response format
apiClient.interceptors.response.use(
  (response) => {
    // Return the response data directly
    return response.data;
  },
  (error) => {
    // Handle different types of errors
    if (error.response?.data) {
      // API returned an error response
      return Promise.reject(error.response.data);
    } else if (error.request) {
      // Network error
      return Promise.reject({
        success: false,
        error: {
          code: 'NETWORK_ERROR',
          message: 'Network error occurred. Please check your connection.',
          technical_message: error.message,
          details: {}
        }
      });
    } else {
      // Other error
      return Promise.reject({
        success: false,
        error: {
          code: 'UNKNOWN_ERROR',
          message: 'An unexpected error occurred.',
          technical_message: error.message,
          details: {}
        }
      });
    }
  }
);

export const pineappleApi = {
  // Quote endpoints
  createQuote: (quoteData) => apiClient.post('/quote', quoteData),
  
  // Transfer endpoints
  createTransfer: (transferData) => apiClient.post('/transfer', transferData),
  
  // Health endpoints
  getHealth: () => apiClient.get('/health'),
  getDebugCors: () => apiClient.get('/debug/cors'),
};

export default pineappleApi;
```

## Custom Hooks

### useApi Hook
Create `src/hooks/useApi.js`:
```javascript
import { useState, useCallback } from 'react';

export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const execute = useCallback(async (apiCall) => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiCall();
      
      if (response.success) {
        return response.data;
      } else {
        setError(response.error);
        return null;
      }
    } catch (err) {
      setError(err.error || {
        code: 'UNKNOWN_ERROR',
        message: 'An unexpected error occurred.',
        technical_message: err.message,
        details: {}
      });
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setError(null);
    setLoading(false);
  }, []);

  return { execute, loading, error, reset };
};
```

### useQuote Hook
Create `src/hooks/useQuote.js`:
```javascript
import { useState } from 'react';
import { useApi } from './useApi';
import { pineappleApi } from '../services/pineappleApi';

export const useQuote = () => {
  const [quote, setQuote] = useState(null);
  const { execute, loading, error, reset } = useApi();

  const createQuote = async (quoteData) => {
    const data = await execute(() => pineappleApi.createQuote(quoteData));
    if (data) {
      setQuote(data);
    }
    return data;
  };

  const resetQuote = () => {
    setQuote(null);
    reset();
  };

  return {
    quote,
    createQuote,
    resetQuote,
    loading,
    error,
  };
};
```

### useTransfer Hook
Create `src/hooks/useTransfer.js`:
```javascript
import { useState } from 'react';
import { useApi } from './useApi';
import { pineappleApi } from '../services/pineappleApi';

export const useTransfer = () => {
  const [transfer, setTransfer] = useState(null);
  const { execute, loading, error, reset } = useApi();

  const createTransfer = async (transferData) => {
    const data = await execute(() => pineappleApi.createTransfer(transferData));
    if (data) {
      setTransfer(data);
      // Optionally redirect to Pineapple
      if (data.redirect_url) {
        window.location.href = data.redirect_url;
      }
    }
    return data;
  };

  const resetTransfer = () => {
    setTransfer(null);
    reset();
  };

  return {
    transfer,
    createTransfer,
    resetTransfer,
    loading,
    error,
  };
};
```

## Component Examples

### QuoteForm Component
Create `src/components/QuoteForm.jsx`:
```javascript
import React from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useQuote } from '../hooks/useQuote';
import ErrorDisplay from './ErrorDisplay';
import LoadingSpinner from './LoadingSpinner';

// Validation schema
const vehicleSchema = z.object({
  make: z.string().min(1, 'Make is required'),
  model: z.string().min(1, 'Model is required'),
  year: z.number().min(1900, 'Invalid year').max(new Date().getFullYear() + 1, 'Invalid year'),
  value: z.number().min(1, 'Value must be greater than 0'),
  engine_size: z.string().optional(),
  fuel_type: z.string().optional(),
  transmission: z.string().optional(),
  vehicle_type: z.string().optional(),
});

const quoteSchema = z.object({
  agentEmail: z.string().email('Invalid email').optional().or(z.literal('')),
  agentBranch: z.string().optional(),
  vehicles: z.array(vehicleSchema).min(1, 'At least one vehicle is required'),
});

const QuoteForm = ({ onQuoteSuccess }) => {
  const { createQuote, loading, error } = useQuote();
  
  const {
    control,
    register,
    handleSubmit,
    formState: { errors },
    reset
  } = useForm({
    resolver: zodResolver(quoteSchema),
    defaultValues: {
      agentEmail: '',
      agentBranch: '',
      vehicles: [{
        make: '',
        model: '',
        year: new Date().getFullYear(),
        value: 0,
        engine_size: '',
        fuel_type: 'Petrol',
        transmission: 'Manual',
        vehicle_type: 'Car'
      }]
    }
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'vehicles'
  });

  const onSubmit = async (data) => {
    // Generate external reference ID
    const externalReferenceId = `QUOTE-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
    
    const quoteData = {
      source: 'SureStrat',
      externalReferenceId,
      agentEmail: data.agentEmail || undefined,
      agentBranch: data.agentBranch || undefined,
      vehicles: data.vehicles.map(vehicle => ({
        ...vehicle,
        year: parseInt(vehicle.year),
        value: parseFloat(vehicle.value)
      }))
    };

    const result = await createQuote(quoteData);
    if (result) {
      onQuoteSuccess?.(result);
      reset();
    }
  };

  const addVehicle = () => {
    append({
      make: '',
      model: '',
      year: new Date().getFullYear(),
      value: 0,
      engine_size: '',
      fuel_type: 'Petrol',
      transmission: 'Manual',
      vehicle_type: 'Car'
    });
  };

  return (
    <div className="quote-form">
      <h2>Request a Quote</h2>
      
      {error && <ErrorDisplay error={error} />}
      
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Agent Information */}
        <div className="agent-info">
          <h3>Agent Information</h3>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="agentEmail">Agent Email</label>
              <input
                {...register('agentEmail')}
                type="email"
                id="agentEmail"
                className={errors.agentEmail ? 'error' : ''}
              />
              {errors.agentEmail && (
                <span className="error-message">{errors.agentEmail.message}</span>
              )}
            </div>
            
            <div className="form-group">
              <label htmlFor="agentBranch">Branch</label>
              <input
                {...register('agentBranch')}
                type="text"
                id="agentBranch"
                className={errors.agentBranch ? 'error' : ''}
              />
              {errors.agentBranch && (
                <span className="error-message">{errors.agentBranch.message}</span>
              )}
            </div>
          </div>
        </div>

        {/* Vehicles */}
        <div className="vehicles-section">
          <h3>Vehicles</h3>
          {fields.map((field, index) => (
            <div key={field.id} className="vehicle-form">
              <div className="vehicle-header">
                <h4>Vehicle {index + 1}</h4>
                {fields.length > 1 && (
                  <button
                    type="button"
                    onClick={() => remove(index)}
                    className="btn-remove"
                  >
                    Remove
                  </button>
                )}
              </div>

              <div className="form-grid">
                <div className="form-group">
                  <label htmlFor={`vehicles.${index}.make`}>Make *</label>
                  <input
                    {...register(`vehicles.${index}.make`)}
                    type="text"
                    className={errors.vehicles?.[index]?.make ? 'error' : ''}
                  />
                  {errors.vehicles?.[index]?.make && (
                    <span className="error-message">
                      {errors.vehicles[index].make.message}
                    </span>
                  )}
                </div>

                <div className="form-group">
                  <label htmlFor={`vehicles.${index}.model`}>Model *</label>
                  <input
                    {...register(`vehicles.${index}.model`)}
                    type="text"
                    className={errors.vehicles?.[index]?.model ? 'error' : ''}
                  />
                  {errors.vehicles?.[index]?.model && (
                    <span className="error-message">
                      {errors.vehicles[index].model.message}
                    </span>
                  )}
                </div>

                <div className="form-group">
                  <label htmlFor={`vehicles.${index}.year`}>Year *</label>
                  <input
                    {...register(`vehicles.${index}.year`, { valueAsNumber: true })}
                    type="number"
                    min="1900"
                    max={new Date().getFullYear() + 1}
                    className={errors.vehicles?.[index]?.year ? 'error' : ''}
                  />
                  {errors.vehicles?.[index]?.year && (
                    <span className="error-message">
                      {errors.vehicles[index].year.message}
                    </span>
                  )}
                </div>

                <div className="form-group">
                  <label htmlFor={`vehicles.${index}.value`}>Value (ZAR) *</label>
                  <input
                    {...register(`vehicles.${index}.value`, { valueAsNumber: true })}
                    type="number"
                    min="1"
                    step="0.01"
                    className={errors.vehicles?.[index]?.value ? 'error' : ''}
                  />
                  {errors.vehicles?.[index]?.value && (
                    <span className="error-message">
                      {errors.vehicles[index].value.message}
                    </span>
                  )}
                </div>

                <div className="form-group">
                  <label htmlFor={`vehicles.${index}.engine_size`}>Engine Size</label>
                  <input
                    {...register(`vehicles.${index}.engine_size`)}
                    type="text"
                    placeholder="e.g., 1.6L"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor={`vehicles.${index}.fuel_type`}>Fuel Type</label>
                  <select {...register(`vehicles.${index}.fuel_type`)}>
                    <option value="Petrol">Petrol</option>
                    <option value="Diesel">Diesel</option>
                    <option value="Hybrid">Hybrid</option>
                    <option value="Electric">Electric</option>
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor={`vehicles.${index}.transmission`}>Transmission</label>
                  <select {...register(`vehicles.${index}.transmission`)}>
                    <option value="Manual">Manual</option>
                    <option value="Automatic">Automatic</option>
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor={`vehicles.${index}.vehicle_type`}>Vehicle Type</label>
                  <select {...register(`vehicles.${index}.vehicle_type`)}>
                    <option value="Car">Car</option>
                    <option value="SUV">SUV</option>
                    <option value="Truck">Truck</option>
                    <option value="Motorcycle">Motorcycle</option>
                  </select>
                </div>
              </div>
            </div>
          ))}

          <button
            type="button"
            onClick={addVehicle}
            className="btn-secondary"
          >
            Add Another Vehicle
          </button>
        </div>

        <div className="form-actions">
          <button
            type="submit"
            disabled={loading}
            className="btn-primary"
          >
            {loading ? <LoadingSpinner /> : 'Get Quote'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default QuoteForm;
```

### TransferForm Component
Create `src/components/TransferForm.jsx`:
```javascript
import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTransfer } from '../hooks/useTransfer';
import ErrorDisplay from './ErrorDisplay';
import LoadingSpinner from './LoadingSpinner';

// South African ID number validation
const validateSAIdNumber = (idNumber) => {
  if (!idNumber || idNumber.length !== 13) return false;
  // Add more sophisticated SA ID validation here
  return /^\d{13}$/.test(idNumber);
};

// Validation schema
const transferSchema = z.object({
  customer_info: z.object({
    first_name: z.string().min(1, 'First name is required'),
    last_name: z.string().min(1, 'Last name is required'),
    email: z.string().email('Invalid email address'),
    contact_number: z.string().min(10, 'Valid phone number required'),
    id_number: z.string().refine(validateSAIdNumber, 'Invalid SA ID number'),
    quote_id: z.string().optional(),
  }),
  agent_info: z.object({
    agent_email: z.string().email('Invalid agent email'),
    branch_name: z.string().min(1, 'Branch name is required'),
  }),
});

const TransferForm = ({ quoteId, onTransferSuccess }) => {
  const { createTransfer, loading, error } = useTransfer();
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset
  } = useForm({
    resolver: zodResolver(transferSchema),
    defaultValues: {
      customer_info: {
        first_name: '',
        last_name: '',
        email: '',
        contact_number: '',
        id_number: '',
        quote_id: quoteId || '',
      },
      agent_info: {
        agent_email: '',
        branch_name: '',
      }
    }
  });

  const onSubmit = async (data) => {
    const result = await createTransfer(data);
    if (result) {
      onTransferSuccess?.(result);
      reset();
    }
  };

  return (
    <div className="transfer-form">
      <h2>Transfer Lead to Pineapple</h2>
      
      {error && <ErrorDisplay error={error} />}
      
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Customer Information */}
        <div className="customer-info">
          <h3>Customer Information</h3>
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="first_name">First Name *</label>
              <input
                {...register('customer_info.first_name')}
                type="text"
                id="first_name"
                className={errors.customer_info?.first_name ? 'error' : ''}
              />
              {errors.customer_info?.first_name && (
                <span className="error-message">
                  {errors.customer_info.first_name.message}
                </span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="last_name">Last Name *</label>
              <input
                {...register('customer_info.last_name')}
                type="text"
                id="last_name"
                className={errors.customer_info?.last_name ? 'error' : ''}
              />
              {errors.customer_info?.last_name && (
                <span className="error-message">
                  {errors.customer_info.last_name.message}
                </span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="email">Email Address *</label>
              <input
                {...register('customer_info.email')}
                type="email"
                id="email"
                className={errors.customer_info?.email ? 'error' : ''}
              />
              {errors.customer_info?.email && (
                <span className="error-message">
                  {errors.customer_info.email.message}
                </span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="contact_number">Phone Number *</label>
              <input
                {...register('customer_info.contact_number')}
                type="tel"
                id="contact_number"
                placeholder="0821234567"
                className={errors.customer_info?.contact_number ? 'error' : ''}
              />
              {errors.customer_info?.contact_number && (
                <span className="error-message">
                  {errors.customer_info.contact_number.message}
                </span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="id_number">ID Number *</label>
              <input
                {...register('customer_info.id_number')}
                type="text"
                id="id_number"
                placeholder="8001015009080"
                maxLength="13"
                className={errors.customer_info?.id_number ? 'error' : ''}
              />
              {errors.customer_info?.id_number && (
                <span className="error-message">
                  {errors.customer_info.id_number.message}
                </span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="quote_id">Quote ID</label>
              <input
                {...register('customer_info.quote_id')}
                type="text"
                id="quote_id"
                readOnly={!!quoteId}
                className={quoteId ? 'readonly' : ''}
              />
            </div>
          </div>
        </div>

        {/* Agent Information */}
        <div className="agent-info">
          <h3>Agent Information</h3>
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="agent_email">Agent Email *</label>
              <input
                {...register('agent_info.agent_email')}
                type="email"
                id="agent_email"
                className={errors.agent_info?.agent_email ? 'error' : ''}
              />
              {errors.agent_info?.agent_email && (
                <span className="error-message">
                  {errors.agent_info.agent_email.message}
                </span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="branch_name">Branch Name *</label>
              <input
                {...register('agent_info.branch_name')}
                type="text"
                id="branch_name"
                className={errors.agent_info?.branch_name ? 'error' : ''}
              />
              {errors.agent_info?.branch_name && (
                <span className="error-message">
                  {errors.agent_info.branch_name.message}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="form-actions">
          <button
            type="submit"
            disabled={loading}
            className="btn-primary"
          >
            {loading ? <LoadingSpinner /> : 'Transfer Lead'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default TransferForm;
```

### ErrorDisplay Component
Create `src/components/ErrorDisplay.jsx`:
```javascript
import React from 'react';

const ErrorDisplay = ({ error, onRetry }) => {
  if (!error) return null;

  const getErrorIcon = (code) => {
    switch (code) {
      case 'TRANSFER_DUPLICATE':
        return '⚠️';
      case 'VALIDATION_ERROR':
        return '❌';
      case 'NETWORK_ERROR':
        return '🌐';
      case 'QUOTE_API_ERROR':
      case 'TRANSFER_API_ERROR':
        return '🔄';
      default:
        return '❗';
    }
  };

  const getErrorClass = (code) => {
    switch (code) {
      case 'TRANSFER_DUPLICATE':
        return 'error-warning';
      case 'VALIDATION_ERROR':
        return 'error-validation';
      case 'NETWORK_ERROR':
        return 'error-network';
      case 'QUOTE_API_ERROR':
      case 'TRANSFER_API_ERROR':
        return 'error-service';
      default:
        return 'error-general';
    }
  };

  const isRetryable = (code) => {
    return ['NETWORK_ERROR', 'QUOTE_API_ERROR', 'TRANSFER_API_ERROR', 
            'QUOTE_STORAGE_ERROR', 'TRANSFER_STORAGE_ERROR'].includes(code);
  };

  const renderValidationErrors = () => {
    if (error.code !== 'VALIDATION_ERROR' || !error.details?.validation_errors) {
      return null;
    }

    return (
      <div className="validation-errors">
        <ul>
          {error.details.validation_errors.map((validationError, index) => (
            <li key={index}>
              <strong>{validationError.field}:</strong> {validationError.message}
            </li>
          ))}
        </ul>
      </div>
    );
  };

  const renderDuplicateError = () => {
    if (error.code !== 'TRANSFER_DUPLICATE') return null;

    const { submission_date, matched_field, source } = error.details;
    const formattedDate = new Date(submission_date).toLocaleDateString('en-ZA', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });

    return (
      <div className="duplicate-error-details">
        <p><strong>Matched Field:</strong> {matched_field}</p>
        <p><strong>Original Submission:</strong> {formattedDate}</p>
        <p><strong>Source:</strong> {source === 'pineapple' ? 'Pineapple System (within 90 days)' : 'Database'}</p>
        {source === 'pineapple' && (
          <p className="info-note">
            This lead is still active in the Pineapple system and cannot be resubmitted within 90 days.
          </p>
        )}
      </div>
    );
  };

  return (
    <div className={`error-display ${getErrorClass(error.code)}`}>
      <div className="error-header">
        <span className="error-icon">{getErrorIcon(error.code)}</span>
        <h4>{error.code.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase())}</h4>
      </div>
      
      <div className="error-content">
        <p className="error-message">{error.message}</p>
        
        {renderValidationErrors()}
        {renderDuplicateError()}
        
        {process.env.NODE_ENV === 'development' && (
          <details className="technical-details">
            <summary>Technical Details (Development Only)</summary>
            <pre>{error.technical_message}</pre>
            {Object.keys(error.details).length > 0 && (
              <pre>{JSON.stringify(error.details, null, 2)}</pre>
            )}
          </details>
        )}
      </div>

      {isRetryable(error.code) && onRetry && (
        <div className="error-actions">
          <button onClick={onRetry} className="btn-retry">
            Try Again
          </button>
        </div>
      )}
    </div>
  );
};

export default ErrorDisplay;
```

### LoadingSpinner Component
Create `src/components/LoadingSpinner.jsx`:
```javascript
import React from 'react';

const LoadingSpinner = ({ size = 'medium', message }) => {
  const sizeClasses = {
    small: 'w-4 h-4',
    medium: 'w-6 h-6',
    large: 'w-8 h-8'
  };

  return (
    <div className="loading-spinner">
      <div className={`spinner ${sizeClasses[size]}`}>
        <div className="animate-spin rounded-full border-2 border-gray-300 border-t-blue-600"></div>
      </div>
      {message && <span className="loading-message">{message}</span>}
    </div>
  );
};

export default LoadingSpinner;
```

### QuoteResult Component
Create `src/components/QuoteResult.jsx`:
```javascript
import React from 'react';

const QuoteResult = ({ quote, onStartTransfer, onNewQuote }) => {
  if (!quote) return null;

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-ZA', {
      style: 'currency',
      currency: 'ZAR',
      minimumFractionDigits: 2
    }).format(amount);
  };

  return (
    <div className="quote-result">
      <div className="result-header">
        <h3>🎉 Quote Generated Successfully!</h3>
        <p className="quote-id">Quote ID: <span>{quote.quoteId}</span></p>
      </div>

      <div className="result-details">
        <div className="detail-card premium">
          <h4>Monthly Premium</h4>
          <p className="amount">{formatCurrency(quote.premium)}</p>
        </div>

        <div className="detail-card excess">
          <h4>Excess</h4>
          <p className="amount">{formatCurrency(quote.excess)}</p>
        </div>
      </div>

      <div className="result-actions">
        <button 
          onClick={() => onStartTransfer(quote.quoteId)}
          className="btn-primary"
        >
          Transfer to Pineapple
        </button>
        
        <button 
          onClick={onNewQuote}
          className="btn-secondary"
        >
          Get New Quote
        </button>
      </div>
    </div>
  );
};

export default QuoteResult;
```

## Error Handling

### Global Error Context
Create `src/contexts/ErrorContext.jsx`:
```javascript
import React, { createContext, useContext, useState } from 'react';

const ErrorContext = createContext();

export const useError = () => {
  const context = useContext(ErrorContext);
  if (!context) {
    throw new Error('useError must be used within an ErrorProvider');
  }
  return context;
};

export const ErrorProvider = ({ children }) => {
  const [errors, setErrors] = useState([]);

  const addError = (error) => {
    const errorWithId = {
      ...error,
      id: Date.now() + Math.random(),
      timestamp: new Date().toISOString()
    };
    setErrors(prev => [...prev, errorWithId]);
  };

  const removeError = (id) => {
    setErrors(prev => prev.filter(error => error.id !== id));
  };

  const clearErrors = () => {
    setErrors([]);
  };

  return (
    <ErrorContext.Provider value={{
      errors,
      addError,
      removeError,
      clearErrors
    }}>
      {children}
    </ErrorContext.Provider>
  );
};
```

### Error Boundary
Create `src/components/ErrorBoundary.jsx`:
```javascript
import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    
    // Log to error reporting service in production
    if (process.env.NODE_ENV === 'production') {
      // Example: Sentry.captureException(error);
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h2>Something went wrong</h2>
          <p>We're sorry, but something unexpected happened.</p>
          <button 
            onClick={() => this.setState({ hasError: false, error: null })}
            className="btn-primary"
          >
            Try Again
          </button>
          {process.env.NODE_ENV === 'development' && (
            <details className="error-details">
              <summary>Error Details (Development)</summary>
              <pre>{this.state.error?.toString()}</pre>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
```

## State Management

### Main App Component
Create `src/App.jsx`:
```javascript
import React, { useState } from 'react';
import { ErrorProvider } from './contexts/ErrorContext';
import ErrorBoundary from './components/ErrorBoundary';
import QuoteForm from './components/QuoteForm';
import TransferForm from './components/TransferForm';
import QuoteResult from './components/QuoteResult';
import LoadingSpinner from './components/LoadingSpinner';
import './App.css';

const App = () => {
  const [currentStep, setCurrentStep] = useState('quote'); // 'quote', 'result', 'transfer'
  const [currentQuote, setCurrentQuote] = useState(null);

  const handleQuoteSuccess = (quote) => {
    setCurrentQuote(quote);
    setCurrentStep('result');
  };

  const handleStartTransfer = (quoteId) => {
    setCurrentStep('transfer');
  };

  const handleTransferSuccess = (transfer) => {
    // Transfer success usually redirects to Pineapple
    // But you can show a success message if needed
    console.log('Transfer successful:', transfer);
  };

  const handleNewQuote = () => {
    setCurrentQuote(null);
    setCurrentStep('quote');
  };

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 'quote':
        return <QuoteForm onQuoteSuccess={handleQuoteSuccess} />;
      
      case 'result':
        return (
          <QuoteResult 
            quote={currentQuote}
            onStartTransfer={handleStartTransfer}
            onNewQuote={handleNewQuote}
          />
        );
      
      case 'transfer':
        return (
          <TransferForm 
            quoteId={currentQuote?.quoteId}
            onTransferSuccess={handleTransferSuccess}
          />
        );
      
      default:
        return <div>Unknown step</div>;
    }
  };

  return (
    <ErrorProvider>
      <ErrorBoundary>
        <div className="app">
          <header className="app-header">
            <h1>Pineapple Insurance Portal</h1>
            <nav className="step-nav">
              <span className={currentStep === 'quote' ? 'active' : ''}>
                1. Quote
              </span>
              <span className={currentStep === 'result' ? 'active' : ''}>
                2. Review
              </span>
              <span className={currentStep === 'transfer' ? 'active' : ''}>
                3. Transfer
              </span>
            </nav>
          </header>

          <main className="app-main">
            {renderCurrentStep()}
          </main>

          <footer className="app-footer">
            <p>&copy; 2025 Surestrat. All rights reserved.</p>
          </footer>
        </div>
      </ErrorBoundary>
    </ErrorProvider>
  );
};

export default App;
```

## TypeScript Support

### Type Definitions
Create `src/types/api.ts`:
```typescript
export interface APIResponse<T> {
  success: boolean;
  data?: T;
  error?: APIError;
  timestamp: string;
}

export interface APIError {
  code: string;
  message: string;
  technical_message: string;
  details: Record<string, any>;
}

export interface Vehicle {
  make: string;
  model: string;
  year: number;
  value: number;
  engine_size?: string;
  fuel_type?: string;
  transmission?: string;
  vehicle_type?: string;
}

export interface QuoteRequest {
  source: 'SureStrat';
  externalReferenceId?: string;
  agentEmail?: string;
  agentBranch?: string;
  vehicles: Vehicle[];
}

export interface QuoteResponse {
  premium: number;
  excess: number;
  quoteId: string;
}

export interface CustomerInfo {
  first_name: string;
  last_name: string;
  email: string;
  contact_number: string;
  id_number: string;
  quote_id?: string;
}

export interface AgentInfo {
  agent_email: string;
  branch_name: string;
}

export interface TransferRequest {
  customer_info: CustomerInfo;
  agent_info: AgentInfo;
}

export interface TransferResponse {
  uuid: string;
  redirect_url: string;
}

export interface ValidationError {
  field: string;
  message: string;
  input: any;
  type: string;
}

export interface DuplicateErrorDetails {
  submission_date: string;
  transfer_id: string;
  matched_field: string;
  source: 'database' | 'pineapple';
}
```

## CSS Styles

Create `src/App.css`:
```css
/* Base styles */
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: #1e40af;
  color: white;
  padding: 1rem 2rem;
}

.app-header h1 {
  margin: 0;
  font-size: 1.5rem;
}

.step-nav {
  display: flex;
  gap: 2rem;
  margin-top: 1rem;
}

.step-nav span {
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
  background: rgba(255, 255, 255, 0.1);
}

.step-nav span.active {
  background: rgba(255, 255, 255, 0.2);
  font-weight: bold;
}

.app-main {
  flex: 1;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.app-footer {
  background: #f3f4f6;
  padding: 1rem 2rem;
  text-align: center;
  color: #6b7280;
}

/* Form styles */
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  font-weight: 500;
  margin-bottom: 0.25rem;
  color: #374151;
}

.form-group input,
.form-group select {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.25rem;
  font-size: 1rem;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-group input.error,
.form-group select.error {
  border-color: #ef4444;
}

.form-group input.readonly {
  background-color: #f9fafb;
  color: #6b7280;
}

.error-message {
  color: #ef4444;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

/* Button styles */
.btn-primary {
  background: #3b82f6;
  color: white;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.25rem;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.btn-secondary {
  background: #6b7280;
  color: white;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.25rem;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-secondary:hover {
  background: #4b5563;
}

.btn-remove {
  background: #ef4444;
  color: white;
  padding: 0.25rem 0.5rem;
  border: none;
  border-radius: 0.25rem;
  font-size: 0.875rem;
  cursor: pointer;
}

.btn-retry {
  background: #f59e0b;
  color: white;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.25rem;
  font-size: 0.875rem;
  cursor: pointer;
}

/* Vehicle form styles */
.vehicle-form {
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1.5rem;
  margin-bottom: 1rem;
}

.vehicle-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.vehicle-header h4 {
  margin: 0;
  color: #374151;
}

/* Quote result styles */
.quote-result {
  text-align: center;
  max-width: 600px;
  margin: 0 auto;
}

.result-header h3 {
  color: #059669;
  margin-bottom: 0.5rem;
}

.quote-id {
  color: #6b7280;
  margin-bottom: 2rem;
}

.quote-id span {
  font-family: monospace;
  background: #f3f4f6;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
}

.result-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.detail-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 1.5rem;
}

.detail-card h4 {
  margin: 0 0 0.5rem 0;
  color: #475569;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.detail-card .amount {
  font-size: 1.5rem;
  font-weight: bold;
  margin: 0;
}

.detail-card.premium .amount {
  color: #059669;
}

.detail-card.excess .amount {
  color: #dc2626;
}

.result-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

/* Error display styles */
.error-display {
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 1rem;
}

.error-warning {
  background: #fef3c7;
  border: 1px solid #f59e0b;
  color: #92400e;
}

.error-validation {
  background: #fee2e2;
  border: 1px solid #ef4444;
  color: #dc2626;
}

.error-network {
  background: #dbeafe;
  border: 1px solid #3b82f6;
  color: #1d4ed8;
}

.error-service {
  background: #fef3c7;
  border: 1px solid #f59e0b;
  color: #92400e;
}

.error-general {
  background: #fee2e2;
  border: 1px solid #ef4444;
  color: #dc2626;
}

.error-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.error-icon {
  font-size: 1.25rem;
}

.error-header h4 {
  margin: 0;
  font-size: 1rem;
}

.error-message {
  margin-bottom: 1rem;
}

.validation-errors ul {
  margin: 0;
  padding-left: 1rem;
}

.duplicate-error-details p {
  margin: 0.25rem 0;
}

.info-note {
  font-style: italic;
  margin-top: 0.5rem;
}

.technical-details {
  margin-top: 1rem;
  font-size: 0.875rem;
}

.technical-details pre {
  background: rgba(0, 0, 0, 0.05);
  padding: 0.5rem;
  border-radius: 0.25rem;
  overflow-x: auto;
}

/* Loading spinner styles */
.loading-spinner {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.spinner {
  display: inline-block;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.loading-message {
  color: #6b7280;
  font-size: 0.875rem;
}

/* Responsive design */
@media (max-width: 768px) {
  .app-main {
    padding: 1rem;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .result-actions {
    flex-direction: column;
  }

  .step-nav {
    flex-direction: column;
    gap: 0.5rem;
  }
}

/* Utility classes */
.space-y-6 > * + * {
  margin-top: 1.5rem;
}

.w-4 { width: 1rem; }
.w-6 { width: 1.5rem; }
.w-8 { width: 2rem; }
.h-4 { height: 1rem; }
.h-6 { height: 1.5rem; }
.h-8 { height: 2rem; }
```

## Best Practices

### 1. Error Handling
- Always check the `success` field before processing data
- Handle specific error codes with appropriate user messages
- Never show technical messages to end users
- Implement retry logic for temporary errors

### 2. Form Validation
- Use Zod for schema validation
- Validate on both client and server side
- Show validation errors near relevant fields
- Provide clear guidance on how to fix errors

### 3. Loading States
- Show loading indicators for async operations
- Disable form submission during loading
- Provide feedback on what's happening

### 4. User Experience
- Use progressive disclosure for complex forms
- Provide clear step indicators
- Show success states prominently
- Handle edge cases gracefully

### 5. Performance
- Use React.memo for components that don't change often
- Implement proper cleanup in useEffect hooks
- Cache API responses when appropriate
- Use debouncing for search inputs

This React integration guide provides everything you need to integrate with the Pineapple Surestrat API in a robust, user-friendly way.
