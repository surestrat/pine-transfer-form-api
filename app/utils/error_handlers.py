"""
Global exception handlers for FastAPI application
"""
from datetime import datetime
from typing import Union, Optional

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.utils.exceptions import APIError
from app.utils.rich_logger import get_rich_logger

logger = get_rich_logger("error_handlers")


def create_error_response(
    error_code: str,
    message: str,
    user_message: str,
    details: Optional[dict] = None,
    status_code: int = 500
) -> JSONResponse:
    """Create standardized error response"""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": error_code,
                "message": user_message,
                "technical_message": message,
                "details": details or {}
            },
            "timestamp": datetime.now().isoformat()
        }
    )


def create_success_response(data: Union[dict, list], status_code: int = 200) -> JSONResponse:
    """Create standardized success response"""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    )


async def api_error_handler(request, exc):
    """Handle custom API errors"""
    # Handle case where detail might be a string or dict
    if isinstance(exc.detail, dict):
        message = exc.detail.get("message", str(exc.detail))
        user_message = exc.detail.get("user_message", message)
        details = exc.detail.get("details", {})
        error_code = getattr(exc, 'error_code', 'API_ERROR')
    else:
        message = str(exc.detail)
        user_message = message
        details = {}
        error_code = getattr(exc, 'error_code', 'API_ERROR')
    
    logger.error(
        f"API Error: {error_code} - {message} - Path: {request.url} - Method: {request.method}"
    )
    
    return create_error_response(
        error_code=error_code,
        message=message,
        user_message=user_message,
        details=details,
        status_code=exc.status_code
    )


async def validation_exception_handler(request, exc):
    """Handle Pydantic validation errors"""
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "input": error.get("input"),
            "type": error.get("type")
        })
    
    logger.warning(
        f"Validation error - Path: {request.url} - Method: {request.method} - Errors: {len(errors)}"
    )
    
    return create_error_response(
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        user_message="Please check the provided data and try again.",
        details={"validation_errors": errors},
        status_code=400
    )


async def pydantic_validation_exception_handler(request, exc):
    """Handle Pydantic ValidationError (different from RequestValidationError)"""
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "input": error.get("input"),
            "type": error.get("type")
        })
    
    logger.warning(
        f"Pydantic validation error - Path: {request.url} - Method: {request.method} - Errors: {len(errors)}"
    )
    
    return create_error_response(
        error_code="VALIDATION_ERROR",
        message="Data validation failed",
        user_message="Please check the provided data and try again.",
        details={"validation_errors": errors},
        status_code=400
    )


async def general_exception_handler(request, exc):
    """Handle unexpected server errors"""
    logger.error(
        f"Unexpected error: {type(exc).__name__}: {str(exc)} - Path: {request.url} - Method: {request.method}",
        exc_info=True
    )
    
    return create_error_response(
        error_code="INTERNAL_SERVER_ERROR",
        message=f"Unexpected error: {type(exc).__name__}: {str(exc)}",
        user_message="An unexpected error occurred. Please try again later.",
        details={"exception_type": type(exc).__name__},
        status_code=500
    )
