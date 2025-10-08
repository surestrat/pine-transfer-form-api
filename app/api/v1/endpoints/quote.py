from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.schemas.quote import QuoteRequest, QuoteResponse, QuoteRetrievalResponse
from app.services.quote import (
    store_quote_request,
    send_quote_request,
    update_quote_response,
    get_quote_by_id,
)
from app.services.email import EmailService
from app.utils.exceptions import (
    QuoteStorageError,
    QuoteAPIError,
    QuoteResponseError
)
import httpx
import logging
from datetime import datetime
from app.utils.rich_logger import get_rich_logger
from config.settings import settings

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
    request_id = quote.externalReferenceId or f"quote-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # Development debugging logs
    if not settings.IS_PRODUCTION:
        logger.info(f"🔍 [DEV] [REQUEST-{request_id}] Starting quote request")
        logger.info(f"🔍 [DEV] [REQUEST-{request_id}] Source: {quote.source}")
        logger.info(f"🔍 [DEV] [REQUEST-{request_id}] Agent: {quote.agentEmail} | Branch: {quote.agentBranch}")
        logger.info(f"🔍 [DEV] [REQUEST-{request_id}] Vehicles count: {len(quote.vehicles)}")

    # Use mode="json" to ensure date fields are serialized as strings
    logger.info(f"Received quote request: {quote.model_dump(mode='json')}")
    
    # Store the quote request
    if not settings.IS_PRODUCTION:
        logger.info(f"💾 [DEV] [REQUEST-{request_id}] Storing quote request")
    
    try:
        created_doc = store_quote_request(quote)
        doc_id = created_doc.get("id") if created_doc else None
        logger.info(f"Stored quote request with doc_id: {doc_id}")
        if not settings.IS_PRODUCTION:
            logger.info(f"✅ [DEV] [REQUEST-{request_id}] Quote stored successfully with ID: {doc_id}")
    except Exception as e:
        if not settings.IS_PRODUCTION:
            logger.error(f"❌ [DEV] [REQUEST-{request_id}] Failed to store quote: {str(e)}")
        logger.error(f"Failed to store quote: {str(e)}")
        raise QuoteStorageError(str(e))

    # Send the quote request to Pineapple
    if not settings.IS_PRODUCTION:
        logger.info(f"🌍 [DEV] [REQUEST-{request_id}] Sending to Pineapple API: {settings.PINEAPPLE_QUOTE_API_URL}")
    
    pineapple_response = await send_quote_request(quote)
    logger.debug(f"Raw response from Pineapple: {pineapple_response}")
    
    if isinstance(pineapple_response, dict) and "error" in pineapple_response:
        if not settings.IS_PRODUCTION:
            logger.error(f"❌ [DEV] [REQUEST-{request_id}] Pineapple API error: {pineapple_response['error']}")
        logger.error(f"Pineapple API error: {pineapple_response['error']}")
        raise QuoteAPIError(pineapple_response['error'])

    if not settings.IS_PRODUCTION:
        logger.info(f"✅ [DEV] [REQUEST-{request_id}] Pineapple API response received")

    # Parse response from send_quote_request
    try:
        pineapple_data_dict: dict

        if isinstance(pineapple_response, httpx.Response):
            try:
                pineapple_data_dict = pineapple_response.json()
                logger.info(f"Parsed Pineapple response: {pineapple_data_dict}")
            except Exception as e:
                logger.error(f"Failed to decode Pineapple response as JSON: {str(e)}")
                raise QuoteResponseError("Invalid JSON from Pineapple API")
        elif isinstance(pineapple_response, dict):
            pineapple_data_dict = pineapple_response
            logger.info(f"Parsed Pineapple response: {pineapple_data_dict}")
        else:
            logger.error(
                f"Unexpected type for pineapple_response: {type(pineapple_response)}. Expected httpx.Response or dict."
            )
            raise QuoteResponseError("Invalid response structure from Pineapple API")

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
            raise QuoteAPIError(str(error_message))

        # Extract premium, excess, and id from the response
        # Based on actual Pineapple response structure:
        # {
        #   "success": true,
        #   "id": "679765d8cdfba62ff342d2ef",
        #   "data": [{"premium": 1240.455614593506, "excess": 6200}]
        # }
        premium = None
        excess = None
        quote_id = None

        # Get the ID from top level
        quote_id = pineapple_data_dict.get("id")
        
        # Get premium and excess from data array
        if "data" in pineapple_data_dict and isinstance(pineapple_data_dict["data"], list) and len(pineapple_data_dict["data"]) > 0:
            first_item = pineapple_data_dict["data"][0]
            if isinstance(first_item, dict):
                premium = first_item.get("premium")
                excess = first_item.get("excess")
                
        # Fallback: check if premium/excess are at top level (for other response formats)
        if premium is None and "premium" in pineapple_data_dict:
            premium = pineapple_data_dict["premium"]
        if excess is None and "excess" in pineapple_data_dict:
            excess = pineapple_data_dict["excess"]

        # If we still can't find the premium, log the problem but continue with zeros
        if premium is None:
            logger.warning(f"Could not find premium in response: {pineapple_data_dict}")
            premium = 0
        if excess is None:
            logger.warning(f"Could not find excess in response: {pineapple_data_dict}")
            excess = 0

        # If quote_id is found, log it in dev mode
        if not settings.IS_PRODUCTION:
            logger.info(f"📊 [DEV] [REQUEST-{request_id}] Parsed quote ID: {quote_id}")
            logger.info(f"📊 [DEV] [REQUEST-{request_id}] Parsed premium: {premium}")
            logger.info(f"📊 [DEV] [REQUEST-{request_id}] Parsed excess: {excess}")

        logger.info(f"Final response to client: premium={premium}, excess={excess}, quoteId={quote_id}")
        
        # Create QuoteResponse object with proper types
        quote_response = QuoteResponse(
            premium=float(premium),
            excess=float(excess),
            quoteId=str(quote_id) if quote_id else None
        )
        
        if not settings.IS_PRODUCTION:
            logger.info(f"💾 [DEV] [REQUEST-{request_id}] Storing quote response...")
        
        if doc_id:
            update_quote_response(doc_id, quote_response)
            logger.info(f"Stored quote response for doc_id: {doc_id}")
        
        if not settings.IS_PRODUCTION:
            logger.info(f"✅ [DEV] [REQUEST-{request_id}] Quote response stored successfully")
            
    except (QuoteStorageError, QuoteAPIError, QuoteResponseError):
        # Re-raise our custom errors
        raise
    except Exception as e:
        if not settings.IS_PRODUCTION:
            logger.error(f"❌ [DEV] [REQUEST-{request_id}] Failed to parse/store response: {str(e)}")
        logger.error(f"Failed to parse or store Pineapple response: {str(e)}")
        raise QuoteResponseError(str(e))

    logger.info(f"📧 [REQUEST-{request_id}] Queuing email notification...")

    # Check if quote notifications are enabled
    if settings.SEND_QUOTE_NOTIFICATIONS:
        # Prepare agent email for CC if available
        agent_email = quote.agentEmail if quote.agentEmail else None
        
        logger.info(f"📧 [REQUEST-{request_id}] Agent CC: {agent_email if agent_email else 'None'}")
        
        # Add BCC if configured
        bcc_emails = settings.ADMIN_BCC_EMAILS if hasattr(settings, 'ADMIN_BCC_EMAILS') and settings.ADMIN_BCC_EMAILS else None
        
        logger.info(f"📧 [REQUEST-{request_id}] Email recipients - TO: {settings.ADMIN_EMAILS}, BCC: {bcc_emails}")
        
        background_tasks.add_task(
            email_service.send_email,
            recipients=settings.ADMIN_EMAILS,  # Use settings directly instead of email_service.admin_emails
            subject="New Quote Request Received",
            template_name="quote_notification.html",
            template_context={
                "quote": quote.model_dump(mode="json"),
                "quote_response": {
                    "premium": premium,
                    "excess": excess,
                    "quoteId": quote_id
                }
            },
            cc=agent_email,
            bcc=bcc_emails
        )
        
        logger.info(f"📧 [REQUEST-{request_id}] Quote notification email queued successfully")
    else:
        logger.warning(f"📧 [REQUEST-{request_id}] Quote notifications DISABLED in settings")

    logger.info(f"🎉 [REQUEST-{request_id}] Quote completed successfully - Premium: {quote_response.premium}")

    return quote_response


@router.get(
    "/quote/{quote_id}",
    response_model=QuoteRetrievalResponse,
    tags=["quote"],
    status_code=200,
)
async def get_quote(quote_id: str):
    """
    Retrieve a quote by its ID.
    
    Args:
        quote_id: The unique identifier of the quote to retrieve
        
    Returns:
        QuoteRetrievalResponse: The quote information including status, vehicles, and pricing
        
    Raises:
        HTTPException: 404 if quote not found, 500 if server error
    """
    logger.info(f"Getting quote with ID: {quote_id}")
    
    if not settings.IS_PRODUCTION:
        logger.info(f"🔍 [DEV] [GET-QUOTE] Retrieving quote ID: {quote_id}")
    
    try:
        # Retrieve quote from database (convert string quote_id to int)
        try:
            quote_id_int = int(quote_id)
        except ValueError:
            if not settings.IS_PRODUCTION:
                logger.warning(f"❌ [DEV] [GET-QUOTE] Invalid quote ID format: {quote_id}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid quote ID format: {quote_id}"
            )
        
        quote_document = get_quote_by_id(quote_id_int)
        
        if not quote_document:
            if not settings.IS_PRODUCTION:
                logger.warning(f"❌ [DEV] [GET-QUOTE] Quote not found: {quote_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Quote with ID {quote_id} not found"
            )
        
        if not settings.IS_PRODUCTION:
            logger.info(f"✅ [DEV] [GET-QUOTE] Quote found: {quote_id}")
            logger.info(f"📊 [DEV] [GET-QUOTE] Status: {quote_document.get('status', 'UNKNOWN')}")
        
        # Handle vehicles field - stored as JSONB in Supabase (already as dict/list)
        vehicles_data = quote_document.get("vehicles", [])
        processed_vehicles = vehicles_data if isinstance(vehicles_data, list) else []
        
        # Build response using Supabase document structure
        quote_response = QuoteRetrievalResponse(
            id=str(quote_document.get("id", quote_id)),
            source=quote_document.get("source", ""),
            internalReference=quote_document.get("internal_reference", ""),
            status=quote_document.get("status", "UNKNOWN"),
            vehicles=processed_vehicles,
            premium=quote_document.get("premium"),
            excess=quote_document.get("excess"),
            quoteId=quote_document.get("quote_id"),
            agentEmail=quote_document.get("agent_email"),
            agentBranch=quote_document.get("agent_branch"),
            created_at=quote_document.get("created_at"),
            updated_at=quote_document.get("updated_at"),
        )
        
        if not settings.IS_PRODUCTION:
            logger.info(f"🎉 [DEV] [GET-QUOTE] Quote retrieved successfully: {quote_id}")
            logger.info(f"📊 [DEV] [GET-QUOTE] Vehicles count: {len(processed_vehicles)}")
        
        logger.info(f"Successfully retrieved quote: {quote_id}")
        return quote_response
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        if not settings.IS_PRODUCTION:
            logger.error(f"❌ [DEV] [GET-QUOTE] Server error retrieving quote {quote_id}: {str(e)}")
        logger.error(f"Server error retrieving quote {quote_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while retrieving quote: {str(e)}"
        )
