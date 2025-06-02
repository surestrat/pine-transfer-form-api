from app.utils.rich_logger import setup_rich_logging
setup_rich_logging()

from fastapi import FastAPI
from app.api.v1.endpoints import quote, transfer

app = FastAPI(title="Pineapple Surestrat API")

# Include routers
app.include_router(quote.router, prefix="/api/v1", tags=["quote"])
app.include_router(transfer.router, prefix="/api/v1", tags=["transfer"])

@app.get("/")
def health_check():
    return {"status": "ok"}

