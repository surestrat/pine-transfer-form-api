from app.utils.rich_logger import setup_rich_logging
from config.settings import settings
import logging

setup_rich_logging()

from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import quote, transfer
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("pine-api")


# Parse ALLOWED_ORIGINS string into a list
def parse_allowed_origins(origins_str: str):
    """Parse comma-separated origins string into a list."""
    if not origins_str:
        return ["*"]  # Default to all origins if empty
    return [origin.strip() for origin in origins_str.split(",") if origin.strip()]


# Use the same parsing logic from your email service
allowed_origins = parse_allowed_origins(settings.ALLOWED_ORIGINS)
logger.info(f"Starting with CORS origins: {allowed_origins}")


class CORSMiddlewareManual(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Handle OPTIONS requests directly
        if request.method == "OPTIONS":
            logger.info(f"Handling OPTIONS preflight request to {request.url.path}")
            response = Response(status_code=200)

            # Get origin from request headers
            origin = request.headers.get("origin", "")
            logger.info(f"Request origin: {origin}")

            # Check if origin is in allowed origins (same as standard middleware)
            allowed_origin = "*" if "*" in allowed_origins else (origin if origin in allowed_origins else "null")
            
            # Add CORS headers using consistent origin policy
            response.headers["Access-Control-Allow-Origin"] = allowed_origin
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, OPTIONS"
            )
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization, X-Requested-With, Accept, Origin"
            )
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Max-Age"] = "86400"

            logger.info(f"OPTIONS response: origin={allowed_origin}")
            return response

        response = await call_next(request)
        return response


app = FastAPI(title="Pineapple Surestrat API")

# Add our custom CORS middleware first (before any routing)
app.add_middleware(CORSMiddlewareManual)

# Now add the standard CORS middleware using the parsed list
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Use the parsed list
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type"],
)

# Include routers
app.include_router(quote.router, prefix="/api/v1", tags=["quote"])
app.include_router(transfer.router, prefix="/api/v1", tags=["transfer"])


# Global OPTIONS handler
@app.options("/{path:path}")
async def options_handler(path: str):
    logger.info(f"Global OPTIONS handler called for path: {path}")
    return Response(status_code=200)


@app.get("/")
def health_check():
    return {"status": "ok", "cors_enabled": True}


@app.get("/health")
def health_check1():
    """
    Health check endpoint to verify the API is running.
    """
    return {"status": "healthy", "cors_enabled": True}


# Add a debug endpoint to check CORS configuration
@app.get("/debug/cors")
def debug_cors():
    """
    Returns the current CORS configuration for debugging.
    """
    return {
        "allowed_origins_raw": settings.ALLOWED_ORIGINS,
        "allowed_origins_parsed": allowed_origins,
        "api_environment": settings.ENVIRONMENT,
        "is_production": settings.IS_PRODUCTION,
    }
