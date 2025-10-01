from fastapi import APIRouter, BackgroundTasks
from app.schemas.transfer import InTransferRequest, ExTransferRequest, TransferResponse
from app.services.transfer import (
    store_transfer_request,
    send_transfer_request,
    update_transfer_response,
    check_existing_transfer,
)
from app.services.email import EmailService
from app.utils.exceptions import (
    TransferDuplicateError,
    TransferStorageError,
    TransferAPIError,
    TransferResponseError
)
import logging
from datetime import datetime
from config.settings import settings

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
    request_id = transfer.customer_info.quote_id or f"transfer-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # Development debugging logs
    if not settings.IS_PRODUCTION:
        logger.info(f"🔍 [DEV] [REQUEST-{request_id}] Starting transfer request")
        logger.info(f"🔍 [DEV] [REQUEST-{request_id}] Customer: {transfer.customer_info.first_name} {transfer.customer_info.last_name}")
        logger.info(f"🔍 [DEV] [REQUEST-{request_id}] Agent: {transfer.agent_info.agent_email} | Branch: {transfer.agent_info.branch_name}")
        logger.info(f"🔍 [DEV] [REQUEST-{request_id}] ID Number: {transfer.customer_info.id_number}")
        logger.info(f"🔍 [DEV] [REQUEST-{request_id}] Contact: {transfer.customer_info.contact_number}")

    # Check for existing transfer by ID number or contact number to prevent duplicates
    if not settings.IS_PRODUCTION:
        logger.info(f"🔍 [DEV] [REQUEST-{request_id}] Checking for duplicate transfers...")
    
    existing_transfer = await check_existing_transfer(
        id_number=transfer.customer_info.id_number,
        contact_number=transfer.customer_info.contact_number,
        request_id=request_id
    )

    if existing_transfer:
        # Get the source and matched field from the duplicate check
        source = existing_transfer.get("source", "database")
        matched_field = existing_transfer.get("matched_field", "ID number")
        
        # Format the submission date
        created_at = existing_transfer.get("created_at", "")
        transfer_id = existing_transfer.get("id", "unknown")

        if not settings.IS_PRODUCTION:
            logger.warning(f"🚫 [DEV] [REQUEST-{request_id}] DUPLICATE DETECTED!")
            logger.warning(f"🚫 [DEV] [REQUEST-{request_id}] Source: {source}")
            logger.warning(f"🚫 [DEV] [REQUEST-{request_id}] Matched field: {matched_field}")
            logger.warning(f"🚫 [DEV] [REQUEST-{request_id}] Original submission: {created_at}")
            logger.warning(f"🚫 [DEV] [REQUEST-{request_id}] Existing transfer ID: {transfer_id}")

        logger.warning(
            f"Duplicate transfer attempt for {matched_field}: {transfer.customer_info.id_number or transfer.customer_info.contact_number}. "
            f"Source: {source}, Transfer ID: {transfer_id}, submitted on: {created_at}"
        )
        
        raise TransferDuplicateError(
            submission_date=created_at,
            transfer_id=str(transfer_id),
            matched_field=matched_field,
            source=source
        )

    # Store the transfer request (with agent/branch info)
    if not settings.IS_PRODUCTION:
        logger.info(f"💾 [DEV] [REQUEST-{request_id}] Storing transfer request in database...")
    
    try:
        created_doc = store_transfer_request(transfer_data=transfer)
        doc_id = created_doc.get("id") if created_doc else None
        if not settings.IS_PRODUCTION:
            logger.info(f"✅ [DEV] [REQUEST-{request_id}] Transfer stored successfully with doc_id: {doc_id}")
    except Exception as e:
        if not settings.IS_PRODUCTION:
            logger.error(f"❌ [DEV] [REQUEST-{request_id}] Failed to store transfer: {str(e)}")
        logger.error(f"Failed to store transfer: {str(e)}")
        raise TransferStorageError(str(e))

    # Prepare ExTransferRequest for external API (includes agent_email & branch_name)
    if not settings.IS_PRODUCTION:
        logger.info(f"🔄 [DEV] [REQUEST-{request_id}] Preparing external API request...")
    
    transfer_request = ExTransferRequest(customer_info=transfer.customer_info, agent_info=transfer.agent_info)

    # Send the transfer request to Pineapple
    if not settings.IS_PRODUCTION:
        logger.info(f"🌍 [DEV] [REQUEST-{request_id}] Sending to Pineapple API: {settings.PINEAPPLE_TRANSFER_API_URL}")
    
    pineapple_response = await send_transfer_request(transfer_request)
    
    if isinstance(pineapple_response, dict) and "error" in pineapple_response:
        if not settings.IS_PRODUCTION:
            logger.error(f"❌ [DEV] [REQUEST-{request_id}] Pineapple API error: {pineapple_response['error']}")
        logger.error(f"Pineapple API error: {pineapple_response['error']}")
        raise TransferAPIError(pineapple_response['error'])

    if not settings.IS_PRODUCTION:
        logger.info(f"✅ [DEV] [REQUEST-{request_id}] Pineapple API response received successfully")

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
        
        if not settings.IS_PRODUCTION:
            logger.info(f"📝 [DEV] [REQUEST-{request_id}] Parsed response - UUID: {transfer_response.uuid}")
            logger.info(f"📝 [DEV] [REQUEST-{request_id}] Redirect URL: {transfer_response.redirect_url}")
        
        # Store the transfer response
        if doc_id:
            update_transfer_response(doc_id, transfer_response)
        
        if not settings.IS_PRODUCTION:
            logger.info(f"💾 [DEV] [REQUEST-{request_id}] Transfer response stored in database")
            
    except Exception as e:
        if not settings.IS_PRODUCTION:
            logger.error(f"❌ [DEV] [REQUEST-{request_id}] Failed to parse/store Pineapple response: {str(e)}")
        logger.error(f"Failed to parse or store Pineapple transfer response: {str(e)}")
        raise TransferResponseError(str(e))

    # Prepare email notification as background task
    if not settings.IS_PRODUCTION:
        logger.info(f"📧 [DEV] [REQUEST-{request_id}] Queuing email notification...")
    
    # Check if transfer notifications are enabled
    if settings.SEND_TRANSFER_NOTIFICATIONS:
        # Prepare agent email for CC if available
        agent_email = transfer.agent_info.agent_email if transfer.agent_info.agent_email else None
        
        if not settings.IS_PRODUCTION and agent_email:
            logger.info(f"📧 [DEV] [REQUEST-{request_id}] Agent will be CC'd: {agent_email}")
        
        # Add BCC if configured
        bcc_emails = settings.ADMIN_BCC_EMAILS if hasattr(settings, 'ADMIN_BCC_EMAILS') and settings.ADMIN_BCC_EMAILS else None
        
        background_tasks.add_task(
            email_service.send_transfer_email,
            recipient=settings.ADMIN_EMAILS,  # Use settings directly instead of email_service.admin_emails
            transfer_data=transfer,
            success=True,
            error_message=None,
            cc=agent_email,
            bcc=bcc_emails
        )
        
        if not settings.IS_PRODUCTION:
            logger.info(f"📧 [DEV] [REQUEST-{request_id}] Transfer notification email queued")
    else:
        if not settings.IS_PRODUCTION:
            logger.info(f"📧 [DEV] [REQUEST-{request_id}] Transfer notifications disabled in settings")

    if not settings.IS_PRODUCTION:
        logger.info(f"🎉 [DEV] [REQUEST-{request_id}] Transfer completed successfully!")
        logger.info(f"🎉 [DEV] [REQUEST-{request_id}] Final UUID: {transfer_response.uuid}")

    return transfer_response
