import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formatdate, make_msgid, formataddr
from email.header import Header
from typing import Optional, List, Union
from config.settings import settings
import logging
from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime, timezone, timedelta
import os
from pathlib import Path

from app.schemas.transfer import InTransferRequest
from app.schemas.email import EmailAttachment

logger = logging.getLogger("email_service")

# South African Standard Time (SAST) is UTC+2
SAST = timezone(timedelta(hours=2))

def get_sast_now() -> datetime:
    """Get current time in South African Standard Time (UTC+2)"""
    return datetime.now(SAST)

# Setup Jinja2 environment for templates
template_env = Environment(
    loader=FileSystemLoader(
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates"
        )
    ),
    autoescape=select_autoescape(["html", "xml"]),
)


class EmailService:
    def __init__(self):
        self.logger = logging.getLogger("email_service")
        self.template_env = template_env
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.email_from = (
            settings.EMAIL_FROM
            if hasattr(settings, "EMAIL_FROM") and settings.EMAIL_FROM
            else self.smtp_username
        )
        # Ensure email_from is always a string and include sender name
        self.email_from = (
            f'"Surestrat - Pineapple system" <{str(self.email_from)}>'
            if self.email_from is not None
            else ""
        )
        self.context = ssl.create_default_context()
        self.admin_emails = settings.ADMIN_EMAILS
        self.logger.info(
            f"SMTP config: server={self.smtp_server}, port={self.smtp_port}, username={self.smtp_username}, from={self.email_from}"
        )

    def render_template(self, template_name: str, context: dict) -> str:
        """
        Render a template with the given context, ensuring 'now' is always available in SAST
        """
        # Add current date in SAST to all templates for footer and date display
        template_context = context.copy() if context else {}
        if "now" not in template_context:
            template_context["now"] = get_sast_now()

        try:
            template = self.template_env.get_template(template_name)
            return template.render(
                **template_context
            )  # Use ** to unpack the dict as keyword args
        except Exception as e:
            self.logger.error(f"Template rendering error for '{template_name}': {str(e)}")
            self.logger.error(f"Template context keys: {list(template_context.keys())}")
            # Return a basic fallback message if template rendering fails
            return f"""
            <html>
            <body>
                <h2>Email Notification</h2>
                <p>An error occurred while rendering the email template '{template_name}'.</p>
                <p>Error details: {str(e)}</p>
                <p>Please contact support if this issue persists.</p>
                <hr>
                <p><small>Context available: {', '.join(template_context.keys())}</small></p>
            </body>
            </html>
            """

    def _parse_recipients(self, recipients: Union[List[str], str]) -> List[str]:
        """
        Parse recipients into a list of email addresses, handling both
        comma-separated strings and lists.
        """
        if not recipients:
            return []

        # If already a list, clean each item
        if isinstance(recipients, list):
            return [email.strip() for email in recipients if email and email.strip()]

        # If a string, could be a single email or comma-separated list
        if isinstance(recipients, str):
            # Handle comma-separated emails
            if "," in recipients:
                return [
                    email.strip() for email in recipients.split(",") if email.strip()
                ]
            else:
                return [recipients.strip()] if recipients.strip() else []

        # Fallback for unexpected types
        self.logger.warning(f"Unexpected recipient format: {type(recipients)}")
        return []

    def _get_recipients_header(self, emails: Union[List[str], str]) -> str:
        """
        Format email addresses for the email header fields (To, CC, BCC).
        Returns a comma-separated string of email addresses.
        """
        email_list = self._parse_recipients(emails)
        return ", ".join(email_list)

    def _strip_html_tags(self, html: str) -> str:
        """Convert HTML to plain text by removing all HTML tags"""
        import re

        return (
            re.sub("<[^<]+?>", "", html).replace("\n", " ").replace("  ", " ").strip()
        )

    def _prepare_message(
        self,
        subject: str,
        recipients: Union[List[str], str],
        html_body: str,
        cc: Optional[Union[List[str], str]] = None,
        bcc: Optional[Union[List[str], str]] = None,
        attachments: Optional[List[EmailAttachment]] = None,
    ) -> MIMEMultipart:
        """Prepare a well-formed MIME message with proper structure for email clients"""
        # Create the root message - a multipart/mixed container
        msg_root = MIMEMultipart("mixed")

        # Set message headers with proper encoding
        msg_root["Subject"] = subject  # MIMEMultipart handles encoding automatically
        msg_root["From"] = str(self.email_from) if self.email_from is not None else ""
        msg_root["To"] = self._get_recipients_header(recipients)
        msg_root["Date"] = formatdate(localtime=True)
        msg_root["Message-ID"] = make_msgid(domain="surestrat.co.za")
        msg_root["MIME-Version"] = "1.0"

        if cc:
            msg_root["Cc"] = self._get_recipients_header(cc)
        if bcc:
            msg_root["Bcc"] = self._get_recipients_header(bcc)

        # Create a multipart/alternative part for the email body
        msg_alternative = MIMEMultipart("alternative")

        # Generate plain text version from HTML
        plain_body = self._strip_html_tags(html_body)

        # First attach the plain text version (as fallback)
        part_plain = MIMEText(plain_body, "plain", "utf-8")
        msg_alternative.attach(part_plain)

        # Then attach the HTML version (preferred)
        part_html = MIMEText(html_body, "html", "utf-8")
        msg_alternative.attach(part_html)

        # Attach the alternative part to the root message
        msg_root.attach(msg_alternative)

        # Handle attachments if provided
        if attachments:
            for attachment in attachments:
                try:
                    # Make sure the file exists
                    file_path = Path(attachment.path)
                    if not file_path.exists():
                        self.logger.error(
                            f"Attachment file not found: {attachment.path}"
                        )
                        continue

                    with open(attachment.path, "rb") as file:
                        part = MIMEApplication(file.read())
                        part.add_header(
                            "Content-Disposition",
                            f"attachment; filename={attachment.filename}",
                        )
                        msg_root.attach(part)
                except Exception as e:
                    self.logger.error(
                        f"Failed to attach file {attachment.filename}: {str(e)}"
                    )

        return msg_root

    def send_email(
        self,
        subject: str,
        recipients: Union[List[str], str],
        template_name: str,
        template_context: Optional[dict] = None,
        cc: Optional[Union[List[str], str]] = None,
        bcc: Optional[Union[List[str], str]] = None,
        attachments: Optional[List[EmailAttachment]] = None,
    ) -> bool:
        """Send an HTML email with plain text fallback using a Jinja2 template"""
        try:
            # Render the HTML body from template
            html_body = self.render_template(template_name, template_context or {})

            # Parse all recipient addresses into clean lists
            to_list = self._parse_recipients(recipients)
            cc_list = self._parse_recipients(cc) if cc else []
            bcc_list = self._parse_recipients(bcc) if bcc else []

            # Combine all recipient lists for the actual sending
            all_recipients = to_list + cc_list + bcc_list

            if not to_list:
                self.logger.error("No valid primary recipients found")
                return False

            # Prepare the complete MIME message
            msg = self._prepare_message(
                subject, to_list, html_body, cc, bcc, attachments
            )

            if not self.smtp_server:
                self.logger.error("SMTP server configuration is missing")
                return False

            self.logger.info(
                f"Connecting to SMTP server {self.smtp_server}:{self.smtp_port} as {self.smtp_username}"
            )
            # Connect to SMTP server and send the message
            with smtplib.SMTP_SSL(
                self.smtp_server, self.smtp_port, context=self.context
            ) as server:
                try:
                    if (
                        self.smtp_username is not None
                        and self.smtp_password is not None
                    ):
                        self.logger.info(
                            f"Attempting SMTP login for user: {self.smtp_username}"
                        )
                        server.login(self.smtp_username, self.smtp_password)
                        self.logger.info("SMTP login successful")
                    else:
                        self.logger.error("SMTP username or password is missing")
                        return False
                except Exception as e:
                    self.logger.error(f"SMTP login failed: {str(e)}")
                    return False

                # Use sendmail instead of send_message for better control
                server.sendmail(
                    from_addr=self.smtp_username,
                    to_addrs=all_recipients,
                    msg=msg.as_string(),
                )

            self.logger.info(f"Email sent successfully to {', '.join(to_list)}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send email: {str(e)}")
            return False

    async def send_transfer_email(
        self,
        recipient: Union[List[str], str],
        transfer_data: InTransferRequest,
        success: bool,
        error_message: Optional[str] = None,
        cc: Optional[Union[List[str], str]] = None,
        bcc: Optional[Union[List[str], str]] = None,
    ) -> bool:
        """Send a transfer notification email"""
        subject = (
            f"Lead Transfer Success: {transfer_data.customer_info.first_name} {transfer_data.customer_info.last_name}"
            if success
            else f"Lead Transfer Failed: {transfer_data.customer_info.first_name} {transfer_data.customer_info.last_name}"
        )
        status_line = (
            "✅ New Report"
            if success
            else f"❌ Lead transfer failed: {error_message or 'Unknown error'}"
        )
        template_context = {
            "transfer": transfer_data,
            "status_line": status_line,
            "success": success,
            "error_message": error_message,
            "now": get_sast_now(),
        }
        return self.send_email(
            subject=subject,
            recipients=recipient,
            template_name="transfer_notification.html",
            template_context=template_context,
            cc=cc,
            bcc=bcc,
        )
