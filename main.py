from app.utils.rich_logger import setup_rich_logging
from config.settings import settings

setup_rich_logging()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import quote, transfer

app = FastAPI(title="Pineapple Surestrat API")

# Include routers
app.include_router(quote.router, prefix="/api/v1", tags=["quote"])
app.include_router(transfer.router, prefix="/api/v1", tags=["transfer"])


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Accept",
        "Origin",
    ],
)


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.get("/health")
def health_check1():
    """
    Health check endpoint to verify the API is running.
    """
    return {"status": "healthy"}
