from fastapi import APIRouter, HTTPException
from app.schemas.lead_payload import LeadPayload
import httpx
import os

router = APIRouter(prefix="/api/v1", tags=["lead"])

@router.post("/lead")
async def proxy_lead(payload: LeadPayload):
    API_URL = os.getenv("PINEAPPLE_API_URL", "")
    API_KEY = os.getenv("API_KEY", "")
    API_SECRET = os.getenv("API_SECRET", "")
    BEARER_TOKEN = f"KEY={API_KEY} SECRET={API_SECRET}"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {BEARER_TOKEN}",
    }

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(API_URL, json=payload.dict(), headers=headers, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            detail = e.response.json().get("detail", str(e))
            raise HTTPException(status_code=e.response.status_code, detail=detail)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))