import httpx

from uuid import uuid4

from config.settings import settings

from typing import Optional, Dict, Any

from app.utils.appwrite import AppwriteService

from appwrite.exception import AppwriteException

from app.schemas.quote import QuoteRequest, QuoteResponse

from app.utils.rich_logger import get_rich_logger

logger = get_rich_logger("Surestrat -> Pineapple -> API {appwrite}")
db = AppwriteService()


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


async def store_quote_request(
    collection_type: str, document_id: str, quote_data: QuoteRequest
):
    try:
        import json

        # NOTE: The 'vehicles' field is stored as a JSON string in Appwrite.
        # When reading from Appwrite, use json.loads(document['vehicles']) to get the list of vehicles.
        quote_data_dict = {
            "source": quote_data.source,
            "externalReferenceId": quote_data.externalReferenceId,
            # Serialize vehicles list to JSON string
            "vehicles": json.dumps(
                [vehicle.model_dump(mode="json") for vehicle in quote_data.vehicles]
            ),
        }
        # Clean None values from payload (not strictly needed for string, but safe)
        flattened_data = clean_dict({**quote_data_dict})
        # Ensure we're passing a dict to create_document
        if not isinstance(flattened_data, dict):
            raise ValueError("Expected a dictionary after cleaning data")
        document = db.create_document(
            data=flattened_data,
            collection_type=collection_type,
            document_id=document_id,
        )
        logger.info(f"Appwrite create_document response: {document}")
        if isinstance(document, dict) and "error" in document:
            raise ValueError(f"Appwrite error: {document['error']}")
        return document
    except AppwriteException as e:
        raise ValueError(f"Failed to store {collection_type} request: {str(e)}")


async def update_quote_response(
    collection_type: str, document_id: str, response_data: QuoteResponse
):
    try:
        # Use model_dump_json to serialize the response as a JSON string, then load as dict
        import json

        update_data = json.loads(response_data.model_dump_json())
        doc = db.update_document(
            document_id=document_id, data=update_data, collection_type=collection_type
        )
        return doc
    except Exception as e:
        logger.error(f"Exception in update_quote_response: {str(e)}")
        raise


async def find_quote_by_phone(
    phone_number: str, request_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Search for a quote by phone number in the quote collection.
    Args:
        phone_number: The phone number to search for
        request_id: Optional ID for logging/tracking
    Returns:
        Optional[Dict[str, Any]]: The quote document if found, None otherwise
    """
    try:
        if not phone_number:
            logger.warning(
                f"[{request_id}] Empty phone number provided for quote search"
            )
            return None

        normalized_phone = (
            phone_number.replace(" ", "").replace("-", "").replace("+", "")
        )

        # Use Query.equal directly in the queries list
        quotes = (
            db.list_documents(
                collection_type="quote",
                fields=None,
            )
            or []
        )  # Default to empty list if None is returned
        # Filter in Python since Appwrite Python SDK does not support Query.equal in list_documents directly
        filtered_quotes = [
            q
            for q in quotes
            if isinstance(q, dict)
            and (q.get("contactNumber", "") or "")
            .replace(" ", "")
            .replace("-", "")
            .replace("+", "")
            == normalized_phone
        ]
        if not filtered_quotes:
            logger.info(
                f"[request_id] No quotes found for phone number {normalized_phone}"
            )
            return None
        # Return the most recent quote document
        newest_quote = sorted(
            filtered_quotes, key=lambda x: x.get("$createdAt", ""), reverse=True
        )[0]
        logger.info(f"[{request_id}] Found quote with ID: {newest_quote.get('$id')}")
        return newest_quote
    except Exception as e:
        logger.error(f"[{request_id}] Error finding quote by phone: {str(e)}")
        return None


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
