from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.schemas.quote import QuoteRequest, QuoteResponse
from app.services.quote import (
    store_quote_request,
    send_quote_request,
    update_quote_response,
)
from app.services.email import EmailService
import httpx
import logging
from app.utils.rich_logger import get_rich_logger

router = APIRouter()
logger = get_rich_logger("quote_endpoint")
email_service = EmailService()


@router.post(
    "/quote",
    response_model=QuoteResponse,
    tags=["quote"],
    status_code=201,
)
async def create_quote(quote: QuoteRequest, background_tasks: BackgroundTasks):
    # Use mode="json" to ensure date fields are serialized as strings
    logger.info(f"Received quote request: {quote.model_dump(mode='json')}")
    # Store the quote request
    doc_id = quote.externalReferenceId
    try:
        try:
            await store_quote_request("quote", doc_id, quote)
            logger.info(f"Stored quote request with doc_id: {doc_id}")
        except Exception as e:
            # If duplicate ID error, use a unique ID
            if "already exists" in str(e):
                from app.utils.appwrite import safe_uuid
                doc_id = safe_uuid()
                logger.warning(f"Duplicate doc_id detected, using unique ID: {doc_id}")
                await store_quote_request("quote", doc_id, quote)
                logger.info(f"Stored quote request with unique doc_id: {doc_id}")
            else:
                logger.error(f"Failed to store quote: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to store quote request")
    except Exception as e:
        logger.error(f"Failed to store quote: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to store quote request")

    # Send the quote request to Pineapple
    pineapple_response = await send_quote_request(quote)
    logger.debug(f"Raw response from Pineapple: {pineapple_response}")
    if isinstance(pineapple_response, dict) and "error" in pineapple_response:
        logger.error(f"Pineapple API error: {pineapple_response['error']}")
        raise HTTPException(
            status_code=502, detail=f"Failed to get quote from Pineapple API: {pineapple_response['error']}"
        )

    # Parse response from send_quote_request
    try:
        pineapple_data_dict: dict

        if isinstance(pineapple_response, httpx.Response):
            try:
                pineapple_data_dict = pineapple_response.json()
                logger.info(f"Parsed Pineapple response: {pineapple_data_dict}")
            except Exception as e:
                logger.error(f"Failed to decode Pineapple response as JSON: {str(e)}")
                raise HTTPException(status_code=502, detail="Invalid JSON from Pineapple API")
        elif isinstance(pineapple_response, dict):
            pineapple_data_dict = pineapple_response
            logger.info(f"Parsed Pineapple response: {pineapple_data_dict}")
        else:
            logger.error(
                f"Unexpected type for pineapple_response: {type(pineapple_response)}. Expected httpx.Response or dict."
            )
            raise HTTPException(
                status_code=502, detail="Invalid response structure from Pineapple API"
            )

        # If Pineapple API returns success: False or http_code != 200, return 502
        if not pineapple_data_dict.get("success", True) or pineapple_data_dict.get("http_code", 200) != 200:
            # Unwrap nested error messages if present
            error_message = pineapple_data_dict.get("error", {})
            if isinstance(error_message, dict) and "message" in error_message:
                error_message = error_message["message"]
                # Unwrap one more level if needed
                if isinstance(error_message, dict) and "message" in error_message:
                    error_message = error_message["message"]
            logger.error(f"Pineapple API error: {error_message}")
            raise HTTPException(
                status_code=502,
                detail=f"Pineapple API error: {error_message}"
            )

        # Extract premium and excess from the response - adjust based on actual response structure
        # The structure might be different from what we expected
        premium = None
        excess = None

        # Check different locations where premium might be stored based on Pineapple API
        if "premium" in pineapple_data_dict:
            premium = pineapple_data_dict["premium"]
        elif "data" in pineapple_data_dict and isinstance(pineapple_data_dict["data"], list) and len(pineapple_data_dict["data"]) > 0:
            first_item = pineapple_data_dict["data"][0]
            if isinstance(first_item, dict):
                premium = first_item.get("premium")
                excess = first_item.get("excess")
        elif "data" in pineapple_data_dict and isinstance(pineapple_data_dict["data"], dict):
            premium = pineapple_data_dict["data"].get("premium")
            excess = pineapple_data_dict["data"].get("excess")

        # If we still can't find the premium, log the problem but continue with zeros
        if premium is None:
            logger.warning(f"Could not find premium in response: {pineapple_data_dict}")
            premium = 0
        if excess is None:
            logger.warning(f"Could not find excess in response: {pineapple_data_dict}")
            excess = 0

        response_data = {
            "premium": float(premium),
            "excess": float(excess),
        }
        logger.info(f"Final response to client: {response_data}")
        quote_response = QuoteResponse(**response_data)
        await update_quote_response("quote", doc_id, quote_response)
        logger.info(f"Stored quote response for doc_id: {doc_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to parse or store Pineapple response: {str(e)}")
        raise HTTPException(
            status_code=502, detail=f"Invalid response from Pineapple API: {str(e)}"
        )

    background_tasks.add_task(
        email_service.send_email,
        recipients=email_service.admin_emails,
        subject="New Quote Request Received",
        template_name="quote_notification.html",
        template_context={"quote": quote.model_dump(mode="json")},
    )

    return quote_response
