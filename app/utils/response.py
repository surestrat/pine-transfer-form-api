"""
Response wrapper utilities for consistent API responses
"""
from datetime import datetime
from typing import Any, Dict, Union, Optional
from fastapi.responses import JSONResponse


def success_response(data: Any, status_code: int = 200) -> Dict[str, Any]:
    """Create a standardized success response"""
    return {
        "success": True,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }


def error_response(
    error_code: str,
    message: str,
    user_message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 500
) -> JSONResponse:
    """Create a standardized error response"""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": error_code,
                "message": user_message or message,
                "technical_message": message,
                "details": details or {}
            },
            "timestamp": datetime.now().isoformat()
        }
    )
