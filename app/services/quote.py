import httpx
import datetime
import json

from uuid import uuid4

from config.settings import settings

from typing import Optional, Dict, Any

from app.utils.supabase import supabase_client

from app.schemas.quote import QuoteRequest, QuoteResponse

from app.utils.rich_logger import get_rich_logger

logger = get_rich_logger("Surestrat -> Pineapple -> API {supabase}")
db = supabase_client


def safe_uuid():
    # Generate a valid short UUID (8 chars, no leading underscore)
    return str(uuid4()).replace("-", "")[:8]


def clean_dict(d):
    """Recursively remove keys with None values from dicts and lists."""
    if isinstance(d, dict):
        return {k: clean_dict(v) for k, v in d.items() if v is not None}
    elif isinstance(d, list):
        return [clean_dict(i) for i in d]
    else:
        return d


def store_quote_request(
    quote_data: QuoteRequest
):
    try:
        # NOTE: In Supabase, vehicles are stored as JSONB (not JSON strings)
        # Convert vehicles to JSON objects for storage
        quote_record = {
            "source": quote_data.source,
            "internal_reference": quote_data.externalReferenceId,
            "status": "PENDING",
            # Store vehicles as JSON array (Supabase will handle JSONB conversion)
            "vehicles": [vehicle.model_dump(mode="json") for vehicle in quote_data.vehicles],
            # Include agent information if provided
            "agent_email": quote_data.agentEmail,
            "agent_branch": quote_data.agentBranch,
        }
        # Clean None values from payload
        flattened_data = clean_dict(quote_record)
        # Ensure we're passing a dict to create_document
        if not isinstance(flattened_data, dict):
            raise ValueError("Expected a dictionary after cleaning data")
        document = db.create_document(
            table=settings.QUOTES_TABLE,
            data=flattened_data,
        )
        logger.info(f"Supabase create_document response: {document}")
        if isinstance(document, dict) and "error" in document:
            raise ValueError(f"Supabase error: {document['error']}")
        return document
    except Exception as e:
        raise ValueError(f"Failed to store quote request: {str(e)}")


def update_quote_response(
    document_id: int, response_data: QuoteResponse
):
    try:
        # Convert premium and excess to strings to match schema
        update_data = {
            "premium": str(response_data.premium) if response_data.premium else None,
            "excess": str(response_data.excess) if response_data.excess else None,
            "status": "COMPLETED"
        }
        
        # Note: quote_id column is optional - only update if available
        # Do not include it in the update if not present to avoid schema errors
        # if response_data.quoteId:
        #     update_data["quote_id"] = response_data.quoteId
            
        doc = db.update_document(
            table=settings.QUOTES_TABLE,
            document_id=document_id,
            data=update_data
        )
        return doc
    except Exception as e:
        logger.error(f"Exception in update_quote_response: {str(e)}")
        raise


def get_quote_by_id(quote_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a quote by its ID from the quote collection.
    Args:
        quote_id: The quote ID to search for
    Returns:
        Optional[Dict[str, Any]]: The quote document if found, None otherwise
    """
    try:
        if not quote_id:
            logger.warning("Empty quote_id provided for quote retrieval")
            return None

        # Get the document directly by ID
        document = db.get_document(
            table=settings.QUOTES_TABLE,
            document_id=quote_id
        )
        
        if document:
            logger.info(f"Retrieved quote with ID: {quote_id}")
            return document
        else:
            logger.info(f"Quote not found with ID: {quote_id}")
            return None
            
    except Exception as e:
        logger.error(f"Error retrieving quote by ID {quote_id}: {str(e)}")
        raise


async def send_quote_request(
    quote_data: QuoteRequest,
    request_id: Optional[str] = None,
):
    try:
        import json  # Ensure json is imported if not already at module level

        update_data = quote_data.model_dump(mode="json")

        # Ensure 'source' is 'SureStrat' (case-sensitive)
        if update_data.get("source"):
            update_data["source"] = "SureStrat"
        else:
            # If source is somehow missing, set it, though Pydantic model should ensure its presence
            update_data["source"] = "SureStrat"

        # Log environment information for debugging
        environment = "PRODUCTION" if settings.IS_PRODUCTION else "TEST"
        logger.info(f"[send_quote_request] Operating in {environment} environment")
        logger.info(
            f"[send_quote_request] Using API endpoint: {settings.PINEAPPLE_QUOTE_API_URL}"
        )

        logger.debug(f"[send_quote_request] Outgoing payload (dict): {update_data}")
        logger.debug(
            f"[send_quote_request] Outgoing payload (JSON): {json.dumps(update_data)}"
        )

        # Construct authorization token exactly as seen in Postman collection
        auth_token = (
            f"KEY={settings.PINEAPPLE_API_KEY} SECRET={settings.PINEAPPLE_API_SECRET}"
        )

        # Mask secrets in logs
        masked_auth = f"KEY={settings.PINEAPPLE_API_KEY[:5]}...{settings.PINEAPPLE_API_KEY[-3:]} SECRET=***"
        logger.info(
            f"[send_quote_request] Using authorization token: Bearer {masked_auth}"
        )
        logger.info(f"[send_quote_request] Outgoing body: {json.dumps(update_data)}")

        api_url = settings.PINEAPPLE_QUOTE_API_URL
        if not api_url:
            logger.error(
                "[send_quote_request] PINEAPPLE_QUOTE_API_URL is not configured"
            )
            raise ValueError(
                "PINEAPPLE_QUOTE_API_URL is not configured"
            )  # This will be caught by the outer except ValueError

        # Inner try-except for the HTTP request itself
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info(f"[send_quote_request] Making POST request to {api_url}")
                response = await client.post(
                    url=api_url,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {auth_token}",
                    },
                    json=update_data,  # httpx handles JSON serialization for the json parameter
                )
                logger.info(
                    f"[send_quote_request] Pineapple response status: {response.status_code}"
                )
                logger.info(
                    f"[send_quote_request] Pineapple response headers: {str(response.headers)}"
                )  # Log headers as string
                logger.info(
                    f"[send_quote_request] Pineapple response body: {response.text}"
                )
                return response
        except httpx.RequestError as exc:  # Catch network errors, timeouts, etc.
            logger.error(
                f"[send_quote_request] HTTP request failed: {exc!r} - URL: {exc.request.url!r}"
            )
            return {"error": f"HTTP request failed: {str(exc)}"}

    # This outer try-except catches ValueErrors (like missing URL) or any other unexpected errors
    except ValueError as ve:
        logger.error(f"[send_quote_request] Configuration or data error: {str(ve)}")
        return {"error": str(ve)}
    except Exception as e:  # Catch any other unexpected errors
        logger.error(
            f"[send_quote_request] Unexpected exception in send_quote_request: {str(e)}"
        )
        return {
            "error": f"An unexpected error occurred in send_quote_request: {str(e)}"
        }
