from fastapi import FastAPI
from .routes.lead import router as lead_router

from dotenv import load_dotenv
import os

from rich.logging import RichHandler
import logging

from fastapi.responses import JSONResponse
import httpx

load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger("pine-transfer-form-api")

logger.debug("Loaded environment variables:")
for k, v in os.environ.items():
    if k in ["API_KEY", "API_SECRET"]:
        logger.debug(f"{k}=***hidden***")
    else:
        logger.debug(f"{k}={v}")

logger.info("Starting FastAPI application.")
logger.debug("Registering routers...")

app = FastAPI()


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}


@app.exception_handler(httpx.RequestError)
async def httpx_request_error_handler(request, exc):
    logger.error(f"HTTPX RequestError: {exc}")
    return JSONResponse(
        status_code=502,
        content={"detail": "Bad gateway: Unable to connect to upstream service."},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.exception("Unhandled exception occurred.")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error."},
    )


app.include_router(lead_router)
logger.debug("lead_router registered.")
