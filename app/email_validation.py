import os
import logging
import smtplib
import ssl

logger = logging.getLogger("pine-api")


def validate_smtp_config():
    """
    Validate SMTP server configuration from environment variables.

    Returns:
        tuple: (is_valid: bool, message: str)
    """
    # Check required environment variables
    smtp_server = os.getenv("SMTP_SERVER") or os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_username = os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS")

    # Validate server and port
    if not smtp_server:
        return False, "SMTP_SERVER environment variable is not set"

    if not smtp_port:
        return False, "SMTP_PORT environment variable is not set"

    try:
        smtp_port = int(smtp_port)
    except ValueError:
        return False, f"SMTP_PORT must be a number, got: {smtp_port}"

    # Validate credentials
    if not smtp_username:
        return False, "SMTP_USERNAME environment variable is not set"

    if not smtp_password:
        return False, "SMTP_PASSWORD environment variable is not set"

    # Validate email lists
    admin_emails = os.getenv("ADMIN_EMAILS", "")
    if not admin_emails.strip():
        logger.warning("ADMIN_EMAILS is empty - no recipients set for notifications")

    return True, "SMTP configuration is valid"


def test_smtp_connection():
    """
    Test connection to the SMTP server.

    Returns:
        tuple: (success: bool, message: str)
    """
    smtp_server = os.getenv("SMTP_SERVER") or os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT") or 465)
    smtp_username = os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS")

    if not smtp_server or not smtp_username or not smtp_password:
        return False, "SMTP configuration incomplete"

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(
            host=smtp_server, port=smtp_port, timeout=10, context=context
        ) as server:
            server.login(smtp_username, smtp_password)
            return True, "SMTP connection test successful"

    except ssl.SSLError as ssl_err:
        return False, f"SSL error: {ssl_err}"
    except smtplib.SMTPAuthenticationError as auth_err:
        return False, f"Authentication failed: {auth_err}"
    except Exception as e:
        return False, f"Connection error: {str(e)}"
