import os
import logging
import smtplib
import ssl
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import List, Optional, Union, Tuple
import asyncio
from dotenv import load_dotenv
from pathlib import Path

# Configure logging
logger = logging.getLogger("pine-api")

# Load environment variables
load_dotenv()


class MailSender:
    """
    Handles email sending via SMTP with support for HTML content and attachments.
    """

    def __init__(
        self,
        in_username: Optional[str] = None,
        in_password: Optional[str] = None,
        in_server: Optional[Union[str, Tuple[str, int]]] = None,
        use_SSL: Optional[bool] = None,
        use_mailgun: Optional[bool] = None,
        timeout: Optional[int] = 30,
    ):
        # Set username
        self.username = (
            in_username or os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER")
        )

        # Set password
        self.password = (
            in_password or os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS")
        )

        # Set server and port
        if isinstance(in_server, tuple):
            self.server, self.port = in_server
        else:
            self.server = (
                in_server or os.getenv("SMTP_SERVER") or os.getenv("SMTP_HOST")
            )
            self.port = int(os.getenv("SMTP_PORT") or 465)

        # Determine if we should use SSL vs STARTTLS based on port if not explicitly specified
        if use_SSL is None:
            # Common SSL ports: 465, 993
            # Common STARTTLS ports: 587, 25, 2525
            self.use_SSL = self.port in (465, 993)
        else:
            self.use_SSL = use_SSL

        # Determine if we should use Mailgun-specific features
        if use_mailgun is None:
            self.use_mailgun = os.getenv("USE_MAILGUN", "false").lower() == "true" or (
                self.server and "mailgun" in self.server.lower()
            )
        else:
            self.use_mailgun = use_mailgun

        # Connection timeout
        self.timeout = timeout or int(os.getenv("SMTP_TIMEOUT") or 30)

        # Initialize connection and message
        self.connection = None
        self.msg = None
        self.to_list = []
        self.cc_list = []
        self.bcc_list = []
        self.from_addr = ""

        logger.info(f"MailSender initialized with server: {self.server}:{self.port}")
        logger.info(
            f"Using {'SSL' if self.use_SSL else 'STARTTLS'} for SMTP connection"
        )
        if self.use_mailgun:
            logger.info("Using Mailgun-specific SMTP implementation")

    def set_message(
        self,
        in_plaintext: str,
        in_subject: str,
        in_from: str,
        in_htmltext: Optional[str] = None,
    ):
        """Set the email message content"""
        self.msg = MIMEMultipart("alternative")
        self.msg["Subject"] = in_subject
        self.from_addr = in_from
        self.msg["From"] = in_from

        # Add plain text part
        part1 = MIMEText(in_plaintext, "plain")
        self.msg.attach(part1)

        # Add HTML part if provided
        if in_htmltext:
            part2 = MIMEText(in_htmltext, "html")
            self.msg.attach(part2)

    def set_recipients(
        self,
        to_list: List[str],
        cc_list: Optional[List[str]] = None,
        bcc_list: Optional[List[str]] = None,
    ):
        """Set email recipients including CC and BCC"""
        # Handle comma-separated email addresses in strings
        self.to_list = []
        if to_list:
            for email in to_list:
                # If an email contains a comma, it might be multiple addresses
                if "," in email:
                    # Split and strip each address
                    self.to_list.extend(
                        [e.strip() for e in email.split(",") if e.strip()]
                    )
                else:
                    self.to_list.append(email.strip())

        # Handle CC list
        self.cc_list = []
        if cc_list:
            for email in cc_list:
                if "," in email:
                    self.cc_list.extend(
                        [e.strip() for e in email.split(",") if e.strip()]
                    )
                else:
                    self.cc_list.append(email.strip())

        # Handle BCC list
        self.bcc_list = []
        if bcc_list:
            for email in bcc_list:
                if "," in email:
                    self.bcc_list.extend(
                        [e.strip() for e in email.split(",") if e.strip()]
                    )
                else:
                    self.bcc_list.append(email.strip())

        # Set headers (for display purposes)
        if self.msg and self.to_list:
            self.msg["To"] = ", ".join(self.to_list)

        if self.msg and self.cc_list:
            self.msg["Cc"] = ", ".join(self.cc_list)

        # BCC is not added to headers but used during sending

        logger.info(
            f"Recipients set - To: {self.to_list}, CC: {self.cc_list}, BCC: {self.bcc_list}"
        )

    def add_attachment(self, file_path: str, filename: Optional[str] = None):
        """Add a file attachment to the email"""
        if not self.msg:
            logger.error("Cannot add attachment - message not initialized")
            return False

        try:
            with open(file_path, "rb") as f:
                part = MIMEApplication(f.read())

            # Set content disposition with filename
            attachment_filename = filename or Path(file_path).name
            part.add_header(
                "Content-Disposition", f"attachment; filename={attachment_filename}"
            )

            self.msg.attach(part)
            return True
        except Exception as e:
            logger.error(f"Failed to add attachment {file_path}: {str(e)}")
            return False

    def connect(self) -> bool:
        """Establish connection to the SMTP server"""
        try:
            if not self.server:
                logger.error("SMTP server address is not defined")
                return False

            logger.info(
                f"Connecting to SMTP server {self.server}:{self.port} (SSL: {self.use_SSL})"
            )

            if self.use_SSL:
                # Use SSL connection (usually port 465)
                context = ssl.create_default_context()
                self.connection = smtplib.SMTP_SSL(
                    host=self.server,
                    port=self.port,
                    timeout=self.timeout,
                    context=context,
                )
            else:
                # Use STARTTLS connection (usually port 587, 25, 2525)
                self.connection = smtplib.SMTP(
                    host=self.server, port=self.port, timeout=self.timeout
                )
                logger.info("Initiating STARTTLS connection")
                self.connection.ehlo()
                if self.connection.has_extn("STARTTLS"):
                    self.connection.starttls()
                    self.connection.ehlo()
                else:
                    logger.warning(
                        "Server does not support STARTTLS, proceeding with unencrypted connection"
                    )

            logger.info(f"Logging in with username: {self.username}")
            if self.username is None or self.password is None:
                logger.error("SMTP username or password is None")
                return False
            self.connection.login(self.username, self.password)
            logger.info(f"Connected to SMTP server {self.server}:{self.port}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to SMTP server: {str(e)}")
            self.connection = None
            return False

    def send_all(self, close_connection: bool = True) -> int:
        """
        Send emails to all recipients

        Returns:
            int: Number of successful sends
        """
        if not self.connection:
            if not self.connect():
                return 0

        if not self.msg:
            logger.error("No message configured to send")
            return 0

        success_count = 0
        all_recipients = self.to_list + self.cc_list + self.bcc_list

        if not all_recipients:
            logger.warning("No recipients specified for email")
            return 0

        try:
            # Double-check connection is not None before sending
            if not self.connection:
                logger.error("Connection is None, cannot send message")
                return 0

            logger.info(f"Sending email to {len(all_recipients)} recipients")
            self.connection.send_message(
                self.msg, from_addr=self.from_addr, to_addrs=all_recipients
            )
            logger.info(f"Email sent successfully to {len(all_recipients)} recipients")
            success_count = len(all_recipients)

        except smtplib.SMTPRecipientsRefused as e:
            # This specific exception has a 'recipients' attribute
            error_msg = str(e)
            logger.error(f"Failed to send email - recipients refused: {error_msg}")
            logger.error(f"Problem recipients: {e.recipients}")
            print(f"Failed to send email: {error_msg}")

        except smtplib.SMTPException as e:
            error_msg = str(e)
            logger.error(f"SMTP error when sending email: {error_msg}")
            print(f"SMTP error: {error_msg}")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"General error when sending email: {error_msg}")
            print(f"Failed to send email: {error_msg}")

        finally:
            if close_connection and self.connection:
                try:
                    self.connection.quit()
                    self.connection = None
                except Exception:
                    pass

        return success_count


async def send_email_async(notification):
    """
    Send email asynchronously
    """
    try:
        return _send_email_with_smtp(notification)
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise


def _send_email_with_smtp(notification):
    """Send email using SMTP"""
    try:
        smtp_username = os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS")
        smtp_server = os.getenv("SMTP_SERVER") or os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT") or 465)
        use_mailgun = os.getenv("USE_MAILGUN", "false").lower() == "true"

        # Determine if we should use SSL based on port
        use_ssl = smtp_port in (465, 993)
        logger.info(
            f"Sending email via {'SSL' if use_ssl else 'STARTTLS'} on port {smtp_port}"
        )

        # Only create the server tuple if smtp_server is not None
        server_param = (smtp_server, smtp_port) if smtp_server else None

        sender = MailSender(
            in_username=smtp_username,
            in_password=smtp_password,
            in_server=server_param,
            use_SSL=use_ssl,  # Use port-based SSL detection instead of hardcoded True
            use_mailgun=use_mailgun,
        )

        # Set the message content
        sender.set_message(
            in_plaintext=notification.body,
            in_subject=notification.subject,
            in_from=f"Pine API <{smtp_username}>",
            in_htmltext=notification.html_body if notification.html_body else None,
        )

        # Set recipients
        sender.set_recipients(
            to_list=notification.recipients,
            cc_list=notification.cc if hasattr(notification, "cc") else None,
            bcc_list=notification.bcc if hasattr(notification, "bcc") else None,
        )

        # Add attachments if any
        if hasattr(notification, "attachments") and notification.attachments:
            for attachment in notification.attachments:
                sender.add_attachment(
                    file_path=attachment.path, filename=attachment.filename
                )

        # Connect and send
        if sender.connect():
            success_count = sender.send_all(close_connection=True)
            if success_count > 0:
                logger.info(f"Email sent successfully to {success_count} recipients")
                return True
            else:
                logger.error("Failed to send email to any recipient")
                return False
        else:
            logger.error("Failed to connect to SMTP server")
            return False

    except Exception as e:
        logger.error(f"Error in _send_email_with_smtp: {str(e)}")
        # Add stack trace for better debugging
        logger.error(f"Stack trace: {traceback.format_exc()}")
        raise


def send_email(notification):
    """
    Synchronous function to send emails that can be called from background tasks
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(send_email_async(notification))
    finally:
        loop.close()
