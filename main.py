from app.utils.rich_logger import setup_rich_logging
from config.settings import settings
import logging

setup_rich_logging()

from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import quote, transfer
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("pine-api")
logger.info(f"Starting with CORS origins: {settings.ALLOWED_ORIGINS}")


class CORSMiddlewareManual(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Handle OPTIONS requests directly
        if request.method == "OPTIONS":
            logger.info(f"Handling OPTIONS preflight request to {request.url.path}")
            response = Response(status_code=200)

            # Get origin from request headers
            origin = request.headers.get("origin", "")
            logger.info(f"Request origin: {origin}")

            # Add CORS headers
            response.headers["Access-Control-Allow-Origin"] = (
                "*"  # For debugging, use "*"
            )
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, OPTIONS"
            )
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization, X-Requested-With, Accept, Origin"
            )
            response.headers["Access-Control-Max-Age"] = (
                "86400"  # Cache preflight for 24 hours
            )

            return response

        # For non-OPTIONS requests, process normally
        response = await call_next(request)

        # For debugging
        logger.debug(
            f"{request.method} {request.url.path} - Response status: {response.status_code}"
        )

        return response


app = FastAPI(title="Pineapple Surestrat API")

# Add our custom CORS middleware first (before any routing)
app.add_middleware(CORSMiddlewareManual)

# Now add the standard CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For debugging purposes, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type"],
)

# Include routers
app.include_router(quote.router, prefix="/api/v1", tags=["quote"])
app.include_router(transfer.router, prefix="/api/v1", tags=["transfer"])


# Global CORS OPTIONS handler for any path
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
