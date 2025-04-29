from fastapi import FastAPI
from .schemas.lead_payload import LeadPayload
from .routes.lead import router as lead_router


app = FastAPI()

app.include_router(lead_router)