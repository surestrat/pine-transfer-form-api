"""
Custom exception classes for structured error handling
"""
from typing import Dict, Any, Optional
from fastapi import HTTPException


class APIError(HTTPException):
    """Base custom API error with structured response"""
    
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        user_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.user_message = user_message or message
        self.details = details or {}
        
        super().__init__(
            status_code=status_code,
            detail={
                "error_code": error_code,
                "message": message,
                "user_message": self.user_message,
                "details": self.details
            }
        )


# Quote-specific errors
class QuoteValidationError(APIError):
    """Raised when quote request validation fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=400,
            error_code="QUOTE_VALIDATION_ERROR",
            message=message,
            user_message="Please check your quote details and try again.",
            details=details
        )


class QuoteStorageError(APIError):
    """Raised when quote cannot be stored in database"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=500,
            error_code="QUOTE_STORAGE_ERROR",
            message=f"Database error: {message}",
            user_message="Unable to save your quote request. Please try again.",
            details=details
        )


class QuoteAPIError(APIError):
    """Raised when Pineapple quote API fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=502,
            error_code="QUOTE_API_ERROR",
            message=f"Pineapple API error: {message}",
            user_message="Unable to process your quote request. Please try again later.",
            details=details
        )


class QuoteResponseError(APIError):
    """Raised when quote response cannot be parsed or stored"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=502,
            error_code="QUOTE_RESPONSE_ERROR", 
            message=f"Invalid response: {message}",
            user_message="Received invalid response from quote service. Please try again.",
            details=details
        )


# Transfer-specific errors
class TransferValidationError(APIError):
    """Raised when transfer request validation fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=400,
            error_code="TRANSFER_VALIDATION_ERROR",
            message=message,
            user_message="Please check your transfer details and try again.",
            details=details
        )


class TransferDuplicateError(APIError):
    """Raised when a duplicate transfer is detected"""
    def __init__(self, submission_date: str, transfer_id: str, matched_field: str, source: str = "database"):
        # Format the date for better readability
        try:
            from datetime import datetime
            if "T" in submission_date:
                dt = datetime.fromisoformat(submission_date.replace("Z", "+00:00"))
                formatted_date = dt.strftime("%B %d, %Y at %H:%M UTC")
            else:
                formatted_date = submission_date
        except:
            formatted_date = submission_date
            
        super().__init__(
            status_code=409,
            error_code="TRANSFER_DUPLICATE",
            message=f"Transfer already exists for this {matched_field} (found in {source})",
            user_message=f"This person has already submitted a transfer request on {formatted_date}.",
            details={
                "submission_date": submission_date,
                "formatted_date": formatted_date,
                "transfer_id": transfer_id,
                "matched_field": matched_field,
                "source": source,  # "database" or "pineapple"
                "retry_allowed": source == "database"  # Only allow retry if it's just a database duplicate
            }
        )


class TransferStorageError(APIError):
    """Raised when transfer cannot be stored in database"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=500,
            error_code="TRANSFER_STORAGE_ERROR",
            message=f"Database error: {message}",
            user_message="Unable to save your transfer request. Please try again.",
            details=details
        )


class TransferAPIError(APIError):
    """Raised when Pineapple transfer API fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=502,
            error_code="TRANSFER_API_ERROR",
            message=f"Pineapple API error: {message}",
            user_message="Unable to process your transfer request. Please try again later.",
            details=details
        )


class TransferResponseError(APIError):
    """Raised when transfer response cannot be parsed or stored"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=502,
            error_code="TRANSFER_RESPONSE_ERROR",
            message=f"Invalid response: {message}",
            user_message="Received invalid response from transfer service. Please try again.",
            details=details
        )


# General system errors
class DatabaseError(APIError):
    """Raised for general database errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=500,
            error_code="DATABASE_ERROR",
            message=f"Database error: {message}",
            user_message="A database error occurred. Please try again later.",
            details=details
        )


class ExternalServiceError(APIError):
    """Raised for external service errors"""
    def __init__(self, service: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR",
            message=f"{service} service error: {message}",
            user_message="External service is temporarily unavailable. Please try again later.",
            details={"service": service, **details} if details else {"service": service}
        )


class EmailError(APIError):
    """Raised when email sending fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=500,
            error_code="EMAIL_ERROR",
            message=f"Email service error: {message}",
            user_message="Notification email could not be sent, but your request was processed successfully.",
            details=details
        )
