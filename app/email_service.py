import os
import smtplib
import logging
import traceback
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("pine-api")


async def send_email(notification):
    try:
        logger.info(
            f"Preparing to send email notification to {len(notification.recipients)} recipients"
        )

        # Get SMTP configuration from environment variables
        # Try multiple possible environment variable names
        smtp_server = os.getenv("SMTP_SERVER") or os.getenv("SMTP_HOST")
        if not smtp_server:
            logger.error("SMTP server not found in environment variables")
            return False

        smtp_port = int(os.getenv("SMTP_PORT") or os.getenv("SMTP_PORT", 465))
        smtp_username = os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS")

        if not smtp_username or not smtp_password:
            logger.error("SMTP credentials not found in environment variables")
            return False

        logger.info(f"Using SMTP server: {smtp_server}:{smtp_port}")

        # Log the email subject and recipients for debugging
        logger.info(f"Email subject: {notification.subject}")
        logger.info(f"Recipients: {notification.recipients}")
        # Connect to SMTP server
        context = ssl.create_default_context()

        try:
            with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
                # Attempt login
                try:
                    server.login(smtp_username, smtp_password)
                    logger.info("SMTP login successful")
                except smtplib.SMTPAuthenticationError as auth_err:
                    logger.error(f"SMTP authentication failed: {auth_err}")
                    return False

                # Send email to each recipient
                success_count = 0
                for recipient in notification.recipients:
                    try:
                        # Create a fresh message for each recipient
                        message = MIMEMultipart()
                        message["From"] = smtp_username
                        message["To"] = recipient
                        message["Subject"] = notification.subject
                        message.attach(MIMEText(notification.body, "plain"))

                        # Send the message
                        server.send_message(message)
                        logger.info(f"Email sent successfully to {recipient}")
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Failed to send email to {recipient}: {str(e)}")

                # Log summary
                logger.info(
                    f"Email sending complete: {success_count}/{len(notification.recipients)} successful"
                )
                return success_count > 0
        except smtplib.SMTPException as smtp_err:
            logger.error(f"SMTP error: {smtp_err}")
            return False
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Unexpected error in send_email: {str(e)}")
        logger.error(traceback.format_exc())
        return False
