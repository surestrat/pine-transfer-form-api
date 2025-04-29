from fastapi import APIRouter, HTTPException
from app.schemas.lead_payload import LeadPayload
import httpx
import os
import logging

logger = logging.getLogger("pine-transfer-form-api")

router = APIRouter(prefix="/api/v1", tags=["lead"])


@router.post("/lead")
async def proxy_lead(payload: LeadPayload):
    API_URL = os.getenv("PINEAPPLE_API_URL", "")
    API_KEY = os.getenv("API_KEY", "")
    API_SECRET = os.getenv("API_SECRET", "")

    if not API_URL or not API_KEY or not API_SECRET:
        logger.error("Missing required environment variables for upstream API.")
        raise HTTPException(
            status_code=500,
            detail="Server misconfiguration: missing upstream API credentials.",
        )

    BEARER_TOKEN = f"KEY={API_KEY} SECRET={API_SECRET}"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {BEARER_TOKEN}",
    }

    logger.debug(f"Received payload: {payload.dict()}")
    logger.debug(f"API_URL: {API_URL}")
    logger.debug(f"Headers: {headers}")

    async with httpx.AsyncClient() as client:
        try:
            logger.debug("Sending POST request to external API...")
            resp = await client.post(
                API_URL, json=payload.dict(), headers=headers, timeout=15
            )
            logger.info(f"Forwarded request to {API_URL}, status: {resp.status_code}")
            logger.debug(f"Request sent with payload: {payload.dict()}")
            logger.debug(f"Response headers: {dict(resp.headers)}")
            logger.debug(f"Response content: {resp.text}")
            resp.raise_for_status()
            logger.debug("Response status OK, returning JSON to client.")
            return resp.json()
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("detail", str(e))
            except Exception:
                detail = str(e)
            logger.error(f"HTTP error: {e.response.status_code} - {detail}")
            logger.debug(f"Error response content: {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=detail)
        except Exception as e:
            logger.exception("Unexpected error occurred while proxying lead.")
            raise HTTPException(status_code=500, detail=str(e))
