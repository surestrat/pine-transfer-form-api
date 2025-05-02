import os
import smtplib
import logging
import traceback
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from socket import timeout as socket_timeout

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
        smtp_timeout = int(
            os.getenv("SMTP_TIMEOUT", 30)
        )  # Default timeout of 30 seconds

        if not smtp_username or not smtp_password:
            logger.error("SMTP credentials not found in environment variables")
            return False

        logger.info(f"Using SMTP server: {smtp_server}:{smtp_port}")

        # Log the email subject and recipients for debugging
        logger.info(f"Email subject: {notification.subject}")
        logger.info(f"Recipients: {notification.recipients}")

        # Create a secure SSL context
        context = ssl.create_default_context()
        # Verify mode for SSL (CERT_REQUIRED is the most secure option)
        context.verify_mode = ssl.CERT_REQUIRED
        # Check hostname to prevent man-in-the-middle attacks
        context.check_hostname = True
        # Load default CA certificates
        context.load_default_certs(purpose=ssl.Purpose.SERVER_AUTH)

        try:
            with smtplib.SMTP_SSL(
                host=smtp_server,
                port=smtp_port,
                local_hostname=None,
                timeout=smtp_timeout,
                context=context,
                source_address=None,
            ) as server:
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
        except socket_timeout as timeout_err:
            logger.error(f"Connection timeout: {timeout_err}")
            return False
        except ssl.CertificateError as cert_err:
            logger.error(f"Certificate verification failed: {cert_err}")
            return False
        except ssl.SSLError as ssl_err:
            logger.error(f"SSL error: {ssl_err}")
            return False
        except smtplib.SMTPConnectError as conn_err:
            logger.error(f"SMTP connection error: {conn_err}")
            return False
        except smtplib.SMTPServerDisconnected as disc_err:
            logger.error(f"SMTP server disconnected: {disc_err}")
            return False
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
