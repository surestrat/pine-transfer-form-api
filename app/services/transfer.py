import httpx
from typing import Optional, Dict, Any

from uuid import uuid4

from app.utils.appwrite import AppwriteService

from config.settings import settings

from app.schemas.transfer import (
    InTransferRequest,
    ExTransferRequest,
    TransferResponse,
)

from app.utils.rich_logger import get_rich_logger
from datetime import datetime
from zoneinfo import ZoneInfo

logger = get_rich_logger("Surestrat -> Pineapple -> API {appwrite}")
db = AppwriteService()


def safe_uuid():
    return str(uuid4()).replace("-", "")[:8]


async def check_existing_transfer_by_id_number(
    id_number: str, request_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Check if a transfer already exists for the given ID number.

    Args:
        id_number: The ID number to check for existing transfers
        request_id: Optional ID for logging/tracking

    Returns:
        Optional[Dict[str, Any]]: The existing transfer document if found, None otherwise
    """
    try:
        if not id_number:
            logger.warning(f"[{request_id}] Empty ID number provided for transfer check")
            return None

        # Clean the ID number (remove spaces, dashes, etc.)
        normalized_id = id_number.replace(" ", "").replace("-", "").strip()

        if not settings.IS_PRODUCTION:
            logger.info(f"🔍 [DEV] [{request_id}] Checking for existing transfer with normalized ID: {normalized_id}")

        logger.info(f"[{request_id}] Checking for existing transfer with ID number: {normalized_id}")

        # Use Appwrite's list_documents to search for existing transfers
        # Note: Appwrite Python SDK has limitations with Query.equal, so we'll filter in Python
        transfers = (
            db.list_documents(
                collection_type="transfer",
                fields=None,
            )
            or []
        )

        # Filter transfers by normalized ID number
        existing_transfers = [
            transfer
            for transfer in transfers
            if isinstance(transfer, dict)
            and transfer.get("id_number", "").replace(" ", "").replace("-", "").strip() == normalized_id
        ]

        if existing_transfers:
            # Return the most recent transfer
            most_recent = sorted(
                existing_transfers,
                key=lambda x: x.get("$createdAt", ""),
                reverse=True
            )[0]

            if not settings.IS_PRODUCTION:
                logger.info(f"✅ [DEV] [{request_id}] Found existing transfer by ID - Transfer ID: {most_recent.get('$id')}")

            logger.info(f"[{request_id}] Found existing transfer with ID {normalized_id}: {most_recent.get('$id')}")
            return most_recent

        if not settings.IS_PRODUCTION:
            logger.info(f"✅ [DEV] [{request_id}] No duplicate found by ID number")

        logger.info(f"[{request_id}] No existing transfer found for ID number: {normalized_id}")
        return None

    except Exception as e:
        logger.error(f"[{request_id}] Error checking for existing transfer: {str(e)}")
        return None


async def check_existing_transfer_by_contact_number(
    contact_number: str, request_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Check if a transfer already exists for the given contact number.

    Args:
        contact_number: The contact number to check for existing transfers
        request_id: Optional ID for logging/tracking

    Returns:
        Optional[Dict[str, Any]]: The existing transfer document if found, None otherwise
    """
    try:
        if not contact_number:
            logger.warning(f"[{request_id}] Empty contact number provided for transfer check")
            return None

        # Clean the contact number (remove spaces, dashes, plus signs, etc.)
        normalized_contact = (
            contact_number.replace(" ", "").replace("-", "").replace("+", "").strip()
        )

        if not settings.IS_PRODUCTION:
            logger.info(f"🔍 [DEV] [{request_id}] Checking for existing transfer with normalized contact: {normalized_contact}")

        logger.info(f"[{request_id}] Checking for existing transfer with contact number: {normalized_contact}")

        # Use Appwrite's list_documents to search for existing transfers
        transfers = (
            db.list_documents(
                collection_type="transfer",
                fields=None,
            )
            or []
        )

        # Filter transfers by normalized contact number
        existing_transfers = [
            transfer
            for transfer in transfers
            if isinstance(transfer, dict)
            and transfer.get("contact_number", "").replace(" ", "").replace("-", "").replace("+", "").strip() == normalized_contact
        ]

        if existing_transfers:
            # Return the most recent transfer
            most_recent = sorted(
                existing_transfers,
                key=lambda x: x.get("$createdAt", ""),
                reverse=True
            )[0]

            if not settings.IS_PRODUCTION:
                logger.info(f"✅ [DEV] [{request_id}] Found existing transfer by contact - Transfer ID: {most_recent.get('$id')}")

            logger.info(f"[{request_id}] Found existing transfer with contact {normalized_contact}: {most_recent.get('$id')}")
            return most_recent

        if not settings.IS_PRODUCTION:
            logger.info(f"✅ [DEV] [{request_id}] No duplicate found by contact number")

        logger.info(f"[{request_id}] No existing transfer found for contact number: {normalized_contact}")
        return None

    except Exception as e:
        logger.error(f"[{request_id}] Error checking for existing transfer by contact: {str(e)}")
        return None


async def check_existing_transfer(
    id_number: Optional[str] = None,
    contact_number: Optional[str] = None,
    request_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Check if a transfer already exists for the given ID number or contact number.

    Args:
        id_number: The ID number to check (optional)
        contact_number: The contact number to check (optional)
        request_id: Optional ID for logging/tracking

    Returns:
        Optional[Dict[str, Any]]: The existing transfer document if found, None otherwise
    """
    # Check by ID number first (more specific)
    if id_number:
        existing_by_id = await check_existing_transfer_by_id_number(id_number, request_id)
        if existing_by_id:
            return existing_by_id

    # Check by contact number if ID number didn't find anything
    if contact_number:
        existing_by_contact = await check_existing_transfer_by_contact_number(contact_number, request_id)
        if existing_by_contact:
            return existing_by_contact

    return None


async def store_transfer_request(
    collection_type: str,
    document_id: str,
    transfer_data: InTransferRequest,
):
    try:
        update_data = {
            "first_name": transfer_data.customer_info.first_name,
            "last_name": transfer_data.customer_info.last_name,
            "email": transfer_data.customer_info.email or "",
            "contact_number": transfer_data.customer_info.contact_number,
            "id_number": transfer_data.customer_info.id_number or "",
            "quote_id": transfer_data.customer_info.quote_id or "",
            "agent_email": transfer_data.agent_info.agent_email,
            "agent_name": transfer_data.agent_info.agent_email,  # Map email to name for backward compatibility
            "branch_name": transfer_data.agent_info.branch_name,
            "created_at": datetime.now(ZoneInfo("Africa/Johannesburg")).isoformat(),
            "updated_at": datetime.now(ZoneInfo("Africa/Johannesburg")).isoformat(),
        }
        document_id = document_id or safe_uuid()

        doc = db.create_document(
            data=update_data, collection_type=collection_type, document_id=document_id
        )
        return doc

    except Exception as e:
        logger.error(f"Exception in store_transfer_request: {str(e)}")
        raise


async def update_transfer_response(
    collection_type: str, document_id: str, response_data: TransferResponse
):
    try:
        update_data = {
            "uuid": response_data.uuid,
            "redirect_url": response_data.redirect_url,
        }

        doc = db.update_document(
            document_id=document_id, data=update_data, collection_type=collection_type
        )
        return doc
    except Exception as e:
        logger.error(f"Exception in update_transfer_response: {str(e)}")
        raise


async def send_transfer_request(
    transfer_data: ExTransferRequest,
):
    """
    Send a transfer request to an external API and store the result.
    """
    try:
        # Important: Create a flat structure exactly as shown in Postman collection
        # The API expects these fields at the root level, not nested in customer_info
        request_payload = {
            "source": "SureStrat",  # Hardcoded to ensure correct casing
            "agentEmail": transfer_data.agent_info.agent_email or "",
            "agentBranch": transfer_data.agent_info.branch_name or "",
            "first_name": transfer_data.customer_info.first_name,
            "last_name": transfer_data.customer_info.last_name,
            "email": transfer_data.customer_info.email or "",
            "id_number": transfer_data.customer_info.id_number or "",
            "quote_id": transfer_data.customer_info.quote_id or "",
            "contact_number": transfer_data.customer_info.contact_number,
        }

        # Log environment information for debugging
        environment = "PRODUCTION" if settings.IS_PRODUCTION else "TEST"
        logger.info(f"[send_transfer_request] Operating in {environment} environment")
        logger.info(
            f"[send_transfer_request] Using API endpoint: {settings.PINEAPPLE_TRANSFER_API_URL}"
        )

        # Construct authorization token exactly as seen in Postman collection
        auth_token = (
            f"KEY={settings.PINEAPPLE_API_KEY} SECRET={settings.PINEAPPLE_API_SECRET}"
        )

        # Mask secrets in logs
        masked_auth = f"KEY={settings.PINEAPPLE_API_KEY[:5]}...{settings.PINEAPPLE_API_KEY[-3:]} SECRET=***"
        logger.info(
            f"[send_transfer_request] Using authorization token: Bearer {masked_auth}"
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info(
                f"[send_transfer_request] Payload to external API: {request_payload}"
            )
            if settings.PINEAPPLE_TRANSFER_API_URL is None:
                raise ValueError("PINEAPPLE_TRANSFER_API_URL is not configured")

            response: httpx.Response = await client.post(
                url=settings.PINEAPPLE_TRANSFER_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {auth_token}",
                },
                json=request_payload,
            )
            logger.info(
                f"[send_transfer_request] Pineapple response status: {response.status_code}"
            )
            logger.info(
                f"[send_transfer_request] Pineapple response headers: {str(response.headers)}"
            )
            logger.info(
                f"[send_transfer_request] Pineapple response body: {response.text}"
            )

            try:
                response_data = response.json()
            except Exception as e:
                logger.error(f"Failed to parse JSON from Pineapple response: {str(e)}")
                return {"error": f"Invalid JSON response: {str(e)}"}
            return response_data

    except Exception as e:
        logger.error(f"Exception in send_transfer_request: {str(e)}")
        return {"error": f"Exception in send_transfer_request: {str(e)}"}
