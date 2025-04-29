from fastapi import FastAPI
from .routes.lead import router as lead_router

from dotenv import load_dotenv
import os

from rich.logging import RichHandler
import logging

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

app.include_router(lead_router)
logger.debug("lead_router registered.")
