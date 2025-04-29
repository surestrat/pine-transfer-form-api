from fastapi import FastAPI
from .routes.lead import router as lead_router


app = FastAPI()

app.include_router(lead_router)
