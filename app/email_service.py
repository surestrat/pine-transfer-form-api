import os
import smtplib
import logging
import traceback
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.utils import formatdate
from email import encoders

# Define COMMASPACE as it's no longer exported from email.utils
COMMASPACE = ", "
from socket import timeout as socket_timeout
from pathlib import Path
from typing import List, Optional, Union, Dict, Any, Tuple

logger = logging.getLogger("pine-api")


class MailSender:
    """
    Contains email contents, connection settings and recipient settings.
    Has functions to compose and send mail. MailSenders are tied to an SMTP server.

    :param in_username: Username for mail server login (required)
    :param in_password: Password for mail server login (required)
    :param in_server: SMTP server to connect to as (server, port) tuple
    :param use_SSL: Select whether to connect over SSL (True) or TLS (False)
    """

    def __init__(
        self, in_username, in_password, in_server=None, use_SSL=True, timeout=30
    ):
        self.username = in_username
        self.password = in_password

        # Use provided server or get from environment
        if in_server:
            self.server_name = in_server[0]
            self.server_port = in_server[1]
        else:
            self.server_name = os.getenv("SMTP_SERVER") or os.getenv("SMTP_HOST")
            self.server_port = int(os.getenv("SMTP_PORT") or 465)

        self.use_SSL = use_SSL
        self.timeout = timeout
        self.connected = False
        self.recipients = []  # Initialize as list
        self.cc_recipients = []
        self.bcc_recipients = []
        self.attachments = []
        self.html_ready = False
        self.msg = None

    def __str__(self):
        return (
            f"Type: Mail Sender\n"
            f"Connection to server {self.server_name}, port {self.server_port}\n"
            f"Connected: {self.connected}\n"
            f"Username: {self.username}, Password: {'*' * len(self.password)}"
        )

    def set_message(
        self,
        in_plaintext,
        in_subject="",
        in_from=None,
        in_htmltext=None,
        attachment=None,
        filename=None,
    ):
        """
        Creates the MIME message to be sent by e-mail. Optionally allows adding subject,
        'from' field, HTML content, and attachments.

        :param in_plaintext: Plaintext email body (required as fallback)
        :param in_subject: Subject line (optional)
        :param in_from: Sender address (optional)
        :param in_htmltext: HTML version of the email body (optional)
        :param attachment: Path to attachment file (optional)
        :param filename: Name for the attachment (optional)
        """
        # Set HTML flag
        self.html_ready = in_htmltext is not None

        # Create the message based on content type
        if self.html_ready:
            self.msg = MIMEMultipart("alternative")
            self.msg.attach(MIMEText(in_plaintext, "plain"))
            # Ensure in_htmltext is not None before attaching
            if in_htmltext is not None:
                self.msg.attach(MIMEText(in_htmltext, "html"))

            # Add attachment if provided
            if attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(open(attachment, "rb").read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={filename or Path(attachment).name}",
                )
                self.msg.attach(part)
        else:
            self.msg = MIMEText(in_plaintext, "plain")

        # Set headers
        self.msg["Subject"] = in_subject
        self.msg["From"] = in_from or self.username
        self.msg["Date"] = formatdate(localtime=True)

    def clear_message(self):
        """Remove the whole email body."""
        if self.msg is None:
            logger.warning("Cannot clear message - message not initialized")
            return

        if self.html_ready:
            # Create a new payload with empty content
            self.msg.set_payload([MIMEText("", "plain"), MIMEText("", "html")])
        else:
            self.msg.set_payload("")

    def set_subject(self, in_subject):
        """Set or update the email subject."""
        if self.msg is None:
            logger.warning("Cannot set subject - message not initialized")
            return

        if hasattr(self.msg, "replace_header"):
            self.msg.replace_header("Subject", in_subject)
        else:
            self.msg["Subject"] = in_subject

    def set_from(self, in_from):
        """Set or update the From field."""
        if self.msg is None:
            logger.warning("Cannot set from - message not initialized")
            return

        if hasattr(self.msg, "replace_header"):
            self.msg.replace_header("From", in_from)
        else:
            self.msg["From"] = in_from

    def set_plaintext(self, in_body_text):
        """
        Set plaintext message: replaces entire payload if no html is used,
        otherwise replaces the plaintext only.

        :param in_body_text: Plaintext email body
        """
        if self.msg is None:
            logger.warning("Cannot set plaintext - message not initialized")
            return

        if not self.html_ready:
            self.msg.set_payload(in_body_text)
        else:
            # Get the current payload
            payload = self.msg.get_payload()

            # Create a new plaintext part
            plaintext_part = MIMEText(in_body_text, "plain")

            # If payload is a list, replace the first item
            if isinstance(payload, list) and len(payload) > 0:
                # Clear existing payload
                self.msg.set_payload([])
                # Attach the new plaintext part
                self.msg.attach(plaintext_part)
                # Re-attach the remaining parts
                for part in payload[1:]:
                    self.msg.attach(part)
            else:
                # If not a list, recreate the multipart structure
                html_part = MIMEText("", "html")  # Empty HTML part as fallback
                self.msg.set_payload([])
                self.msg.attach(plaintext_part)
                self.msg.attach(html_part)

    def set_html(self, in_html):
        """
        Replace HTML version of the email body. The plaintext version is unaffected.

        :param in_html: HTML email body
        """
        if self.msg is None:
            logger.warning("Cannot set HTML - message not initialized")
            return

        if not self.html_ready:
            logger.warning(
                "Attempting to set HTML content for a plain text message. "
                "Use set_message with in_htmltext parameter first."
            )
            # Convert to multipart/alternative
            if self.msg is None:
                plaintext = ""
                self.msg = MIMEMultipart("alternative")
                self.msg.attach(MIMEText(plaintext, "plain"))
            else:
                plaintext = str(self.msg.get_payload())
                self.msg = MIMEMultipart("alternative")
                self.msg.attach(MIMEText(plaintext, "plain"))
            self.msg.attach(MIMEText(in_html, "html"))
            self.html_ready = True
        else:
            payload = self.msg.get_payload()
            if isinstance(payload, list) and len(payload) > 1:
                # Replace the HTML part in the payload list
                html_part = MIMEText(in_html, "html")
                payload[1] = html_part
                self.msg.set_payload(payload)
            else:
                # If payload is not a list or doesn't have enough elements, recreate the structure
                plaintext = ""
                if isinstance(payload, list) and len(payload) > 0:
                    # Safely extract plaintext content
                    try:
                        # Check if the payload is a MIMEText or similar object with get_payload method
                        if hasattr(payload[0], "get_payload"):
                            # Make sure it's not None and has the get_payload method
                            if isinstance(
                                payload[0], (MIMEText, MIMEMultipart)
                            ) and callable(getattr(payload[0], "get_payload", None)):
                                plaintext_content = payload[0].get_payload()
                                if plaintext_content is not None:
                                    # Handle both string and list payloads
                                    if isinstance(plaintext_content, str):
                                        plaintext = plaintext_content
                                    else:
                                        plaintext = str(plaintext_content)
                            else:
                                plaintext = str(payload[0])
                        else:
                            # If it's not a MIME object with get_payload, convert to string
                            plaintext = str(payload[0])
                    except (AttributeError, IndexError, TypeError) as e:
                        logger.warning(f"Error extracting plaintext content: {e}")
                        plaintext = ""
                elif isinstance(payload, str):
                    plaintext = payload

                # Ensure plaintext is a string
                if not isinstance(plaintext, str):
                    plaintext = str(plaintext)

                # Clear and rebuild the multipart structure
                self.msg.set_payload([])
                self.msg.attach(MIMEText(plaintext, "plain"))
                self.msg.attach(MIMEText(in_html, "html"))

    def add_attachment(self, attachment_path, custom_filename=None):
        """
        Add a file attachment to the email.

        :param attachment_path: Path to the file to attach
        :param custom_filename: Custom filename to use (optional)
        """
        if not self.msg:
            logger.error("Cannot add attachment - message not initialized")
            return

        try:
            # Ensure we have a multipart message
            if not self.html_ready and not isinstance(self.msg, MIMEMultipart):
                # Convert simple message to multipart
                content = self.msg.get_payload()
                content_type = self.msg.get_content_type()
                headers = dict(self.msg.items())

                self.msg = MIMEMultipart("mixed")

                # Restore headers
                for key, value in headers.items():
                    if key not in ["Content-Type", "Content-Transfer-Encoding"]:
                        self.msg[key] = value

                # Add the original content - ensure content is a string
                if not isinstance(content, str):
                    content = str(content)
                self.msg.attach(MIMEText(content, content_type.split("/")[1]))

            # Create attachment part
            part = MIMEBase("application", "octet-stream")

            with open(attachment_path, "rb") as file:
                part.set_payload(file.read())

            encoders.encode_base64(part)
            filename = custom_filename or Path(attachment_path).name
            part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.msg.attach(part)
            logger.info(f"Added attachment: {filename}")

        except Exception as e:
            logger.error(f"Failed to add attachment {attachment_path}: {str(e)}")

    def set_recipients(self, in_recipients):
        """
        Sets the list of recipient email addresses.

        :param in_recipients: List of recipient email addresses
        """
        if not isinstance(in_recipients, (list, tuple)):
            raise TypeError(
                f"Recipients must be a list or tuple, is {type(in_recipients)}"
            )

        # Always store as a list to ensure we can append
        self.recipients = list(in_recipients)
        if self.msg:
            if len(in_recipients) > 0:
                self.msg["To"] = COMMASPACE.join(in_recipients)

    def set_cc(self, cc_recipients):
        """
        Sets the list of CC recipient email addresses.

        :param cc_recipients: List of CC recipient email addresses
        """
        if not isinstance(cc_recipients, (list, tuple)):
            raise TypeError(
                f"CC recipients must be a list or tuple, is {type(cc_recipients)}"
            )

        self.cc_recipients = cc_recipients
        if self.msg and len(cc_recipients) > 0:
            self.msg["Cc"] = COMMASPACE.join(cc_recipients)

    def set_bcc(self, bcc_recipients):
        """
        Sets the list of BCC recipient email addresses.

        :param bcc_recipients: List of BCC recipient email addresses
        """
        if not isinstance(bcc_recipients, (list, tuple)):
            raise TypeError(
                f"BCC recipients must be a list or tuple, is {type(bcc_recipients)}"
            )

        # Convert to list to ensure we can append later
        self.bcc_recipients = list(bcc_recipients)
        if self.msg and len(bcc_recipients) > 0:
            self.msg["Bcc"] = COMMASPACE.join(bcc_recipients)

    def add_recipient(self, in_recipient):
        """
        Adds a recipient to the list.

        :param in_recipient: Recipient email address
        """
        # Ensure recipients is a list before appending
        if not isinstance(self.recipients, list):
            self.recipients = list(self.recipients)

        self.recipients.append(in_recipient)
        if self.msg:
            if "To" in self.msg:
                if hasattr(self.msg, "replace_header"):
                    self.msg.replace_header("To", COMMASPACE.join(self.recipients))
                else:
                    self.msg["To"] = COMMASPACE.join(self.recipients)
            else:
                self.msg["To"] = COMMASPACE.join(self.recipients)

    def add_cc(self, cc_recipient):
        """
        Adds a CC recipient to the list.

        :param cc_recipient: CC recipient email address
        """
        # Ensure cc_recipients is a list before appending
        if not isinstance(self.cc_recipients, list):
            self.cc_recipients = list(self.cc_recipients)

        self.cc_recipients.append(cc_recipient)
        if self.msg:
            if "Cc" in self.msg:
                if hasattr(self.msg, "replace_header"):
                    self.msg.replace_header("Cc", COMMASPACE.join(self.cc_recipients))
                else:
                    self.msg["Cc"] = COMMASPACE.join(self.cc_recipients)
            else:
                self.msg["Cc"] = COMMASPACE.join(self.cc_recipients)

    def add_bcc(self, bcc_recipient):
        """
        Adds a BCC recipient to the list.

        :param bcc_recipient: BCC recipient email address
        """
        self.bcc_recipients.append(bcc_recipient)
        # BCC is not added to headers as it should not be visible in the message

    def connect(self):
        """
        Connects to SMTP server using the username and password.
        Must be called before sending messages.
        """
        try:
            # Create SSL context if using SSL
            context = None
            if self.use_SSL:
                context = ssl.create_default_context()

            # Ensure server_name is not None
            if not self.server_name:
                raise ValueError("SMTP server name cannot be None")

            # Create the appropriate server connection
            if self.use_SSL:
                self.smtpserver = smtplib.SMTP_SSL(
                    host=self.server_name,
                    port=self.server_port,
                    timeout=self.timeout,
                    context=context,
                )
            else:
                self.smtpserver = smtplib.SMTP(
                    host=self.server_name, port=self.server_port, timeout=self.timeout
                )
                self.smtpserver.starttls(context=context)

            # Login to the server
            self.smtpserver.login(self.username, self.password)
            self.connected = True
            logger.info(f"Connected to {self.server_name}")
            return True

        except ssl.SSLError as ssl_err:
            logger.error(f"SSL error when connecting: {ssl_err}")
            return False
        except smtplib.SMTPAuthenticationError as auth_err:
            logger.error(f"SMTP authentication failed: {auth_err}")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to SMTP server: {str(e)}")
            return False

    def disconnect(self):
        """Close the connection to the SMTP server."""
        if self.connected:
            try:
                self.smtpserver.quit()
                self.connected = False
                logger.info("Disconnected from SMTP server")
            except Exception as e:
                logger.error(f"Error disconnecting from SMTP server: {str(e)}")

    def send_all(self, close_connection=True):
        """
        Sends message to all specified recipients, one at a time.

        :param close_connection: Whether to close the connection after sending
        :return: Number of successfully sent emails
        """
        if not self.connected:
            raise ConnectionError("Not connected to any server. Try connect() first")

        if not self.msg:
            raise ValueError("No message set. Try set_message() first")

        if not self.recipients:
            raise ValueError("No recipients set. Try set_recipients() first")

        logger.info(f"Sending to {len(self.recipients)} recipients")

        success_count = 0
        for recipient in self.recipients:
            try:
                # Create a copy of the message for each recipient
                message_copy = self.msg
                if hasattr(message_copy, "replace_header"):
                    message_copy.replace_header("To", recipient)
                else:
                    message_copy["To"] = recipient

                # Determine all recipients for SMTP send
                all_recipients = (
                    [recipient] + list(self.cc_recipients) + list(self.bcc_recipients)
                )

                # Send the message
                self.smtpserver.send_message(
                    message_copy,
                    from_addr=message_copy["From"],
                    to_addrs=all_recipients,
                )
                logger.info(f"Email sent successfully to {recipient}")
                success_count += 1

            except Exception as e:
                logger.error(f"Failed to send email to {recipient}: {str(e)}")

        logger.info(
            f"Email sending complete: {success_count}/{len(self.recipients)} successful"
        )

        if close_connection:
            self.disconnect()

        return success_count


async def send_email(notification):
    """
    Send an email notification to recipients using the MailSender class.

    Args:
        notification: Email notification object with subject, body, recipients
                     and optional html_body, cc, bcc, attachments

    Returns:
        bool: True if at least one email was sent successfully, False otherwise
    """
    try:
        # Extract email settings from environment
        smtp_username = os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS")
        smtp_server = os.getenv("SMTP_SERVER") or os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT") or 465)
        smtp_timeout = int(os.getenv("SMTP_TIMEOUT", 30))

        # Create recipients list
        recipients_count = len(notification.recipients)
        cc_count = (
            len(notification.cc)
            if hasattr(notification, "cc") and notification.cc
            else 0
        )
        bcc_count = (
            len(notification.bcc)
            if hasattr(notification, "bcc") and notification.bcc
            else 0
        )

        logger.info(
            f"Preparing to send email notification to {recipients_count} recipients, "
            f"{cc_count} CC recipients, and {bcc_count} BCC recipients"
        )

        # Check for required settings
        if not smtp_server or not smtp_username or not smtp_password:
            logger.error(
                "SMTP settings not configured properly in environment variables"
            )
            return False

        # Create and configure mail sender
        mail_sender = MailSender(
            in_username=smtp_username,
            in_password=smtp_password,
            in_server=(smtp_server, smtp_port),
            use_SSL=True,
            timeout=smtp_timeout,
        )

        # Set message content
        html_body = getattr(notification, "html_body", None)

        # Log the email content for debugging (only in development)
        logger.debug(f"Email plain text content: {notification.body[:100]}...")
        if html_body:
            logger.debug(f"Email HTML content preview: {html_body[:100]}...")

        # Create the email message
        mail_sender.set_message(
            in_plaintext=notification.body,
            in_subject=notification.subject,
            in_htmltext=html_body,
        )

        # Set recipients
        mail_sender.set_recipients(notification.recipients)

        # Set CC and BCC if available
        if hasattr(notification, "cc") and notification.cc:
            mail_sender.set_cc(notification.cc)

        if hasattr(notification, "bcc") and notification.bcc:
            mail_sender.set_bcc(notification.bcc)

        # Add attachments if available
        if hasattr(notification, "attachments") and notification.attachments:
            for attachment in notification.attachments:
                if isinstance(attachment, dict):
                    path = attachment.get("path")
                    filename = attachment.get("filename")
                else:
                    # Handle Pydantic model objects
                    path = attachment.path
                    filename = attachment.filename

                if path and os.path.exists(path):
                    mail_sender.add_attachment(path, filename)
                else:
                    logger.warning(f"Attachment not found at path: {path}")

        # Connect to the server
        logger.info(f"Attempting to connect to SMTP server: {smtp_server}:{smtp_port}")
        if mail_sender.connect():
            # Send emails
            logger.info("SMTP connection successful, sending emails")
            success_count = mail_sender.send_all(close_connection=True)
            return success_count > 0
        else:
            logger.error("Failed to connect to SMTP server")
            return False

    except Exception as e:
        logger.error(f"Unexpected error in send_email: {str(e)}")
        logger.error(traceback.format_exc())
        return False
