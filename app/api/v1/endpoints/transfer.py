from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.schemas.transfer import InTransferRequest, ExTransferRequest, TransferResponse
from app.services.transfer import (
    store_transfer_request,
    send_transfer_request,
    update_transfer_response,
    check_existing_transfer,
)
from app.services.email import EmailService
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
        # Format the submission date
        created_at = existing_transfer.get("$createdAt", "")
        if created_at:
            try:
                # Parse the ISO timestamp and format it nicely
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            except:
                formatted_date = created_at
        else:
            formatted_date = "unknown date"

        # Determine which field matched
        matched_field = "ID number"
        if transfer.customer_info.id_number and existing_transfer.get("id_number") == transfer.customer_info.id_number:
            matched_field = "ID number"
        elif transfer.customer_info.contact_number and existing_transfer.get("contact_number") == transfer.customer_info.contact_number:
            matched_field = "contact number"

        if not settings.IS_PRODUCTION:
            logger.warning(f"🚫 [DEV] [REQUEST-{request_id}] DUPLICATE DETECTED!")
            logger.warning(f"🚫 [DEV] [REQUEST-{request_id}] Matched field: {matched_field}")
            logger.warning(f"🚫 [DEV] [REQUEST-{request_id}] Original submission: {formatted_date}")
            logger.warning(f"🚫 [DEV] [REQUEST-{request_id}] Existing transfer ID: {existing_transfer.get('$id')}")

        logger.warning(
            f"Duplicate transfer attempt for {matched_field}: {transfer.customer_info.id_number or transfer.customer_info.contact_number}. "
            f"Existing transfer ID: {existing_transfer.get('$id')}, submitted on: {formatted_date}"
        )
        raise HTTPException(
            status_code=409,
            detail=f"Transfer already exists for this {matched_field}. "
                   f"Existing transfer ID: {existing_transfer.get('$id')}, "
                   f"submitted on: {formatted_date}"
        )

    # Store the transfer request (with agent/branch info)
    if not settings.IS_PRODUCTION:
        logger.info(f"💾 [DEV] [REQUEST-{request_id}] Storing transfer request in database...")
    
    try:
        doc_id = transfer.customer_info.quote_id or ""
        await store_transfer_request(
            collection_type="transfer", document_id=doc_id, transfer_data=transfer
        )
        if not settings.IS_PRODUCTION:
            logger.info(f"✅ [DEV] [REQUEST-{request_id}] Transfer stored successfully with doc_id: {doc_id}")
    except Exception as e:
        if not settings.IS_PRODUCTION:
            logger.error(f"❌ [DEV] [REQUEST-{request_id}] Failed to store transfer: {str(e)}")
        logger.error(f"Failed to store transfer: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to store transfer request")

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
        raise HTTPException(
            status_code=502, detail="Failed to transfer lead to Pineapple API"
        )

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
        await update_transfer_response("transfer", doc_id, transfer_response)
        
        if not settings.IS_PRODUCTION:
            logger.info(f"💾 [DEV] [REQUEST-{request_id}] Transfer response stored in database")
            
    except Exception as e:
        if not settings.IS_PRODUCTION:
            logger.error(f"❌ [DEV] [REQUEST-{request_id}] Failed to parse/store Pineapple response: {str(e)}")
        logger.error(f"Failed to parse or store Pineapple transfer response: {str(e)}")
        raise HTTPException(
            status_code=502, detail="Invalid response from Pineapple API"
        )

    # Prepare email notification as background task
    if not settings.IS_PRODUCTION:
        logger.info(f"📧 [DEV] [REQUEST-{request_id}] Queuing email notification...")
    
    # Prepare agent email for CC if available
    agent_email = transfer.agent_info.agent_email if transfer.agent_info.agent_email else None
    
    if not settings.IS_PRODUCTION and agent_email:
        logger.info(f"📧 [DEV] [REQUEST-{request_id}] Agent will be CC'd: {agent_email}")
    
    background_tasks.add_task(
        email_service.send_transfer_email,
        recipient=email_service.admin_emails,
        transfer_data=transfer,
        success=True,
        error_message=None,
        cc=agent_email,
    )

    if not settings.IS_PRODUCTION:
        logger.info(f"🎉 [DEV] [REQUEST-{request_id}] Transfer completed successfully!")
        logger.info(f"🎉 [DEV] [REQUEST-{request_id}] Final UUID: {transfer_response.uuid}")

    return transfer_response
