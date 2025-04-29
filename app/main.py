from fastapi import FastAPI
from .routes.lead import router as lead_router

# Add logging and dotenv
from loguru import logger
from dotenv import load_dotenv

load_dotenv()
logger.add("logs/app.log", rotation="1 MB", retention="10 days", level="DEBUG")

app = FastAPI()

logger.info("Starting FastAPI application.")

app.include_router(lead_router)
