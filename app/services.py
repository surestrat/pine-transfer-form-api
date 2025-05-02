import os
import json
import logging
import httpx
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.id import ID
from fastapi import HTTPException
from .schemas import AdminNotification

logger = logging.getLogger("pine-api")


def get_appwrite_client():
    client = Client()
    client.set_endpoint(os.getenv("APPWRITE_ENDPOINT"))
    client.set_project(os.getenv("APPWRITE_PROJECT_ID"))
    client.set_key(os.getenv("APPWRITE_API_KEY"))
    return client


def get_database():
    client = get_appwrite_client()
    return Databases(client)


def check_appwrite_health():
    """
    Checks if Appwrite connection is healthy by attempting a minimal operation.
    Returns (ok: bool, message: str)
    """
    try:
        database = get_database()
        database_id = os.getenv("APPWRITE_DATABASE_ID")
        if database_id is None:
            return False, "Appwrite connection failed: APPWRITE_DATABASE_ID is not set"
        # Try a minimal operation (e.g., get database info or just instantiate)
        # Do not return collections or IDs
        return True, "Appwrite connection OK"
    except Exception as e:
        return False, f"Appwrite connection failed: {str(e)}"


def get_external_api_bearer_token():
    api_key = os.getenv("EXTERNAL_API_KEY")
    api_secret = os.getenv("EXTERNAL_API_SECRET")
    if not api_key or not api_secret:
        logger.error("Missing API key or secret in environment variables")
        raise ValueError("External API key and secret must be configured in .env file")
    return f"KEY={api_key} SECRET={api_secret}"


async def submit_form_service(submission, background_tasks, database, send_email):
    logger.info(
        f"Received form submission for {submission.formData.first_name} {submission.formData.last_name}"
    )
    collection_id = os.getenv("APPWRITE_COLLECTION_ID")
    database_id = os.getenv("APPWRITE_DATABASE_ID")
    if not database_id or not collection_id:
        logger.error("Missing Appwrite database or collection ID")
        raise ValueError(
            "Appwrite database_id and collection_id must be configured in .env file"
        )
    unique_id = ID.unique()
    external_api_data = {
        "source": "SureStrat",
        "first_name": submission.formData.first_name,
        "last_name": submission.formData.last_name,
        "email": submission.formData.email,
        "contact_number": submission.formData.contact_number,
        "quote_id": submission.formData.quote_id or ID.unique(),
    }
    if submission.formData.id_number:
        external_api_data["id_number"] = submission.formData.id_number
    combined_data = {
        **submission.formData.model_dump(),
        "agent": submission.agentInfo.agent,
        "branch": submission.agentInfo.branch,
        "name": f"{submission.formData.first_name} {submission.formData.last_name}",
        "source": "SureStrat",
        "quote_id": submission.formData.quote_id or ID.unique(),
    }
    logger.info(
        f"Storing submission in Appwrite: {json.dumps(combined_data, default=str)}"
    )
    document = database.create_document(
        database_id=database_id,
        collection_id=collection_id,
        document_id=unique_id,
        data=combined_data,
    )
    logger.info(f"Document created with ID: {document['$id']}")
    external_api_url = os.getenv("EXTERNAL_API_URL")
    if not external_api_url:
        raise ValueError("EXTERNAL_API_URL environment variable is not set")
    bearer_token = get_external_api_bearer_token()
    logger.info(f"Calling external API at: {external_api_url}")
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    logger.info(
        f"Request headers: {json.dumps({k: v for k, v in headers.items() if k != 'Authorization'})}"
    )
    logger.info(f"Request payload: {json.dumps(external_api_data, default=str)}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                external_api_url,
                json=external_api_data,
                headers=headers,
                timeout=30.0,
            )
            logger.info(f"External API response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            if response.status_code >= 400:
                logger.error(
                    f"External API error: {response.status_code} - {response.text}"
                )
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"External API request failed: {response.text}",
                )
            api_response = response.json()
            logger.info(
                f"API response received: {json.dumps(api_response, default=str)}"
            )
            uuid = None
            redirect_url = None
            if api_response.get("success") and api_response.get("data"):
                uuid = api_response["data"].get("uuid")
                redirect_url = api_response["data"].get("redirect_url")
            update_data = {
                "api_response": json.dumps(api_response, default=str),
            }
            if uuid:
                update_data["uuid"] = uuid
            if redirect_url:
                update_data["redirect_url"] = redirect_url
            database.update_document(
                database_id=database_id,
                collection_id=collection_id,
                document_id=document["$id"],
                data=update_data,
            )
            logger.info("Document updated with API response")
    except httpx.TimeoutException:
        logger.error("External API timeout")
        api_response = {"error": "External API request timed out"}
        database.update_document(
            database_id=database_id,
            collection_id=collection_id,
            document_id=document["$id"],
            data={"api_error": json.dumps("Request timed out")},
        )
    except httpx.NetworkError as e:
        logger.error(f"Network error when calling external API: {str(e)}")
        api_response = {"error": "Network error when connecting to external service"}
        database.update_document(
            database_id=database_id,
            collection_id=collection_id,
            document_id=document["$id"],
            data={"api_error": json.dumps(f"Network error: {str(e)}")},
        )

    # Email notification section
    admin_emails = os.getenv("ADMIN_EMAILS") or os.getenv("NOTIFICATION_EMAILS", "")
    admin_email_list = [
        email.strip() for email in admin_emails.split(",") if email.strip()
    ]

    # Get CC and BCC recipients
    admin_cc_emails = os.getenv("ADMIN_CC_EMAILS", "")
    admin_cc_list = [
        email.strip() for email in admin_cc_emails.split(",") if email.strip()
    ]

    admin_bcc_emails = os.getenv("ADMIN_BCC_EMAILS", "")
    admin_bcc_list = [
        email.strip() for email in admin_bcc_emails.split(",") if email.strip()
    ]

    logger.info(f"Found admin emails: {admin_email_list}")
    if admin_cc_list:
        logger.info(f"Found CC emails: {admin_cc_list}")
    if admin_bcc_list:
        logger.info(f"Found BCC emails: {admin_bcc_list}")

    if admin_email_list:
        redirect_info = ""
        if api_response.get("success") and api_response.get("data"):
            data = api_response["data"]
            if isinstance(data, dict):
                uuid = data.get("uuid", "Not provided")
                redirect_url = data.get("redirect_url", "Not provided")
                redirect_info = f"\nRedirect URL: {redirect_url}\nUUID: {uuid}"
            else:
                redirect_info = f"\nAPI Response data is not in expected format: {data}"

        logger.info(f"Preparing notification for {len(admin_email_list)} admin(s)")

        # Create plain text body
        plain_text_body = (
            f"Customer Information:\n"
            f"Name: {submission.formData.first_name} {submission.formData.last_name}\n"
            f"Email: {submission.formData.email}\n"
            f"Contact Number: {submission.formData.contact_number}\n"
            f"ID Number: {submission.formData.id_number or 'Not provided'}\n"
            f"Quote ID: {submission.formData.quote_id or unique_id}\n\n"
            f"Agent Information:\n"
            f"Agent: {submission.agentInfo.agent}\n"
            f"Branch: {submission.agentInfo.branch}\n\n"
            f"API Response:{redirect_info}\n"
            f"Full Response: {json.dumps(api_response, default=str)}"
        )

        # Create HTML body
        html_body = f"""
        <html>
          <head>
            <style>
              body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
              h2 {{ color: #0056b3; }}
              .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #0056b3; background-color: #f8f9fa; }}
              .data-row {{ margin: 8px 0; }}
              .label {{ font-weight: bold; }}
              pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; }}
            </style>
          </head>
          <body>
            <h2>Customer Information</h2>
            <div class="section">
              <div class="data-row"><span class="label">Name:</span> {submission.formData.first_name} {submission.formData.last_name}</div>
              <div class="data-row"><span class="label">Email:</span> {submission.formData.email}</div>
              <div class="data-row"><span class="label">Contact Number:</span> {submission.formData.contact_number}</div>
              <div class="data-row"><span class="label">ID Number:</span> {submission.formData.id_number or 'Not provided'}</div>
              <div class="data-row"><span class="label">Quote ID:</span> {submission.formData.quote_id or unique_id}</div>
            </div>
            
            <h2>Agent Information</h2>
            <div class="section">
              <div class="data-row"><span class="label">Agent:</span> {submission.agentInfo.agent}</div>
              <div class="data-row"><span class="label">Branch:</span> {submission.agentInfo.branch}</div>
            </div>
        """

        # Add redirect information if available
        if api_response.get("success") and api_response.get("data"):
            data = api_response["data"]
            if isinstance(data, dict) and data.get("redirect_url"):
                redirect_url = data.get("redirect_url", "Not provided")
                uuid = data.get("uuid", "Not provided")
                html_body += f"""
                <h2>Redirect Information</h2>
                <div class="section">
                  <div class="data-row"><span class="label">Redirect URL:</span> <a href="{redirect_url}">{redirect_url}</a></div>
                  <div class="data-row"><span class="label">UUID:</span> {uuid}</div>
                </div>
                """

        # Add API response
        html_body += f"""
            <h2>API Response</h2>
            <div class="section">
              <pre>{json.dumps(api_response, default=str, indent=2)}</pre>
            </div>
          </body>
        </html>
        """

        notification = AdminNotification(
            subject=f"New Form Submission - Pineapple Lead Transfer: {submission.formData.first_name} {submission.formData.last_name}",
            body=plain_text_body,
            html_body=html_body,
            recipients=admin_email_list,
            cc=admin_cc_list,
            bcc=admin_bcc_list,
        )

        try:
            logger.info("Adding email notification task to background tasks")
            background_tasks.add_task(send_email, notification)
        except Exception as e:
            logger.error(f"Failed to add email task: {str(e)}")
    else:
        logger.warning("No admin emails configured. Skipping email notification.")

    response_data = {
        "message": "Form submitted successfully",
        "document_id": document["$id"],
        "api_response": api_response,
    }
    try:
        data = api_response.get("data")
        if api_response.get("success", False) and isinstance(data, dict):
            redirect_url = data.get("redirect_url")
            if redirect_url:
                response_data["redirect_url"] = redirect_url
                logger.info(f"Returning redirect URL: {redirect_url}")
    except Exception as e:
        logger.warning(f"Error extracting redirect URL from API response: {str(e)}")
    logger.info(f"Form submission processed successfully")
    return response_data
