import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


async def send_email(notification):
    smtp_server = os.getenv("SMTP_SERVER")
    if not smtp_server:
        raise ValueError("SMTP server must be configured in .env file")
    smtp_port = int(os.getenv("SMTP_PORT", 465))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    if not smtp_username or not smtp_password:
        raise ValueError("SMTP username and password must be configured in .env file")
    message = MIMEMultipart()
    message["From"] = smtp_username or "noreply@example.com"
    message["Subject"] = notification.subject
    message.attach(MIMEText(notification.body, "plain"))
    with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
        server.login(smtp_username, smtp_password)
        for recipient in notification.recipients:
            message["To"] = recipient
            server.send_message(message)
