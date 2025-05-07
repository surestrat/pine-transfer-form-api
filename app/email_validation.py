import os
import logging
import smtplib
import ssl
from dotenv import load_dotenv

logger = logging.getLogger("pine-api")
load_dotenv()


def validate_smtp_config():
    """
    Validate that SMTP configuration is present in environment variables

    Returns:
        tuple: (is_valid, message)
    """
    smtp_username = os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS")
    smtp_server = os.getenv("SMTP_SERVER") or os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")

    if not smtp_server:
        return False, "SMTP server not configured. Set SMTP_SERVER in .env"

    if not smtp_username:
        return False, "SMTP username not configured. Set SMTP_USERNAME in .env"

    if not smtp_password:
        return False, "SMTP password not configured. Set SMTP_PASSWORD in .env"

    if not smtp_port:
        logger.warning("SMTP port not configured, will use default")

    return True, "SMTP configuration is valid"


def test_smtp_connection():
    """
    Test the SMTP connection to verify credentials and server availability

    Returns:
        tuple: (is_successful, message)
    """
    smtp_username = os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER") or ""
    smtp_password = os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS") or ""
    smtp_server = os.getenv("SMTP_SERVER") or os.getenv("SMTP_HOST") or ""
    smtp_port = int(os.getenv("SMTP_PORT") or 465)

    # Determine if we should use SSL based on port
    use_ssl = smtp_port in (465, 993)

    try:
        if use_ssl:
            # Use SSL connection (usually port 465)
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(
                host=smtp_server, port=smtp_port, timeout=10, context=context
            )
        else:
            # Use STARTTLS connection (usually port 587, 25, 2525)
            server = smtplib.SMTP(host=smtp_server, port=smtp_port, timeout=10)
            server.ehlo()
            if server.has_extn("STARTTLS"):
                server.starttls()
                server.ehlo()
            else:
                logger.warning(
                    "Server does not support STARTTLS, proceeding with unencrypted connection"
                )

        # Attempt login
        server.login(smtp_username, smtp_password)
        server.quit()
        return True, "SMTP connection successful"

    except ssl.SSLError as e:
        logger.error(f"SSL error: {str(e)}")
        # If SSL failed and we were trying to use SSL, suggest trying STARTTLS instead
        if use_ssl:
            return (
                False,
                f"SSL error: {str(e)}. Try using port 587 for STARTTLS instead of SSL.",
            )
        return False, f"SSL error: {str(e)}"

    except smtplib.SMTPAuthenticationError:
        return False, "SMTP authentication failed. Check username and password."

    except smtplib.SMTPConnectError:
        return False, "Failed to connect to SMTP server. Check server address and port."

    except smtplib.SMTPException as e:
        return False, f"SMTP error: {str(e)}"

    except Exception as e:
        return False, f"Error connecting to SMTP server: {str(e)}"
