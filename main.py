from app.utils.rich_logger import setup_rich_logging
from config.settings import settings
import logging
from datetime import datetime

setup_rich_logging()

from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from app.api.v1.endpoints import quote, transfer
from app.utils.exceptions import APIError
from app.utils.error_handlers import (
    api_error_handler,
    validation_exception_handler,
    pydantic_validation_exception_handler,
    general_exception_handler
)
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("pine-api")

# Simple CORS configuration - allow all origins
logger.info("Starting with CORS enabled for all origins (*)")

app = FastAPI(title="Pineapple Surestrat API")

# Register exception handlers
app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Simple CORS middleware - allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Must be False when allow_origins is ["*"]
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Include routers
app.include_router(quote.router, prefix="/api/v1", tags=["quote"])
app.include_router(transfer.router, prefix="/api/v1", tags=["transfer"])


@app.get("/")
def health_check():
    return {"success": True, "data": {"status": "ok", "cors_enabled": True}, "timestamp": datetime.now().isoformat()}


@app.get("/health")
def health_check1():
    """
    Health check endpoint to verify the API is running.
    """
    return {"success": True, "data": {"status": "healthy", "cors_enabled": True}, "timestamp": datetime.now().isoformat()}


# Add a debug endpoint to check CORS configuration
@app.get("/debug/cors")
def debug_cors():
    """
    Returns the current CORS configuration for debugging.
    """
    return {
        "success": True,
        "data": {
            "allowed_origins": "*",
            "api_environment": settings.ENVIRONMENT,
            "is_production": settings.IS_PRODUCTION,
            "note": "CORS is configured to allow all origins"
        },
        "timestamp": datetime.now().isoformat()
    }
