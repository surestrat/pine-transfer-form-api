import httpx

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

logger = get_rich_logger("Surestrat -> Pineapple -> API {appwrite}")
db = AppwriteService()


def safe_uuid():
    return str(uuid4()).replace("-", "")[:8]


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
            "agent_name": transfer_data.agent_info.agent_name,
            "branch_name": transfer_data.agent_info.branch_name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
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
