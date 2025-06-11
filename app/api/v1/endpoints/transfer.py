from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.schemas.transfer import InTransferRequest, ExTransferRequest, TransferResponse
from app.services.transfer import (
    store_transfer_request,
    send_transfer_request,
    update_transfer_response,
)
from app.services.email import EmailService
import logging

router = APIRouter()
logger = logging.getLogger("transfer_endpoint")
email_service = EmailService()


@router.post(
    "/transfer",
    response_model=TransferResponse,
    tags=["transfer"],
    status_code=201,
)
async def create_transfer(
    transfer: InTransferRequest, background_tasks: BackgroundTasks
):
    # Store the transfer request (with agent/branch info)
    try:
        doc_id = transfer.customer_info.quote_id or ""
        await store_transfer_request(
            collection_type="transfer", document_id=doc_id, transfer_data=transfer
        )
    except Exception as e:
        logger.error(f"Failed to store transfer: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to store transfer request")

    # Prepare ExTransferRequest for external API (exclude agent_name & Branch_name)
    transfer_request = ExTransferRequest(customer_info=transfer.customer_info)

    # Send the transfer request to Pineapple
    pineapple_response = await send_transfer_request(transfer_request)
    if isinstance(pineapple_response, dict) and "error" in pineapple_response:
        logger.error(f"Pineapple API error: {pineapple_response['error']}")
        raise HTTPException(
            status_code=502, detail="Failed to transfer lead to Pineapple API"
        )

    # Parse response (assuming JSON with uuid/redirect_url)
    try:
        data = (
            pineapple_response.get("data", {})
            if isinstance(pineapple_response, dict)
            else {}
        )
        transfer_response = TransferResponse(
            uuid=data.get("uuid", "") if isinstance(data, dict) else "",
            redirect_url=data.get("redirect_url", "") if isinstance(data, dict) else "",
        )
        # Store the transfer response
        await update_transfer_response("transfer", doc_id, transfer_response)
    except Exception as e:
        logger.error(f"Failed to parse or store Pineapple transfer response: {str(e)}")
        raise HTTPException(
            status_code=502, detail="Invalid response from Pineapple API"
        )

    # Prepare email notification as background task
    background_tasks.add_task(
        email_service.send_transfer_email,
        recipient=email_service.admin_emails,
        transfer_data=transfer,
        success=True,
        error_message=None,
    )

    return transfer_response
