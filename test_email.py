"""
Quick test script to verify the email service functionality.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.email_service import MailSender
from app.email_validation import validate_smtp_config, test_smtp_connection


def test_mail_sender():
    """Test the MailSender class directly"""
    print("Testing MailSender class...")

    # Get SMTP settings from environment variables
    load_dotenv()
    smtp_username = os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS")
    smtp_server = os.getenv("SMTP_SERVER") or os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT") or 465)

    # Get test recipient
    test_recipient = input("Enter test recipient email: ")

    # Create MailSender instance
    sender = MailSender(
        in_username=smtp_username,
        in_password=smtp_password,
        in_server=(smtp_server, smtp_port),
        use_SSL=True,
    )

    # Create test message
    plaintext = (
        "Hello,\n\nThis is a test email from the Pine API.\n\nRegards,\nThe System"
    )
    html = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; }
            .container { padding: 20px; border: 1px solid #ccc; border-radius: 5px; }
            .heading { color: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2 class="heading">Test Email</h2>
            <p>Hello,</p>
            <p>This is a <b>test email</b> from the Pine API.</p>
            <p>Regards,<br>The System</p>
        </div>
    </body>
    </html>
    """

    sender.set_message(
        in_plaintext=plaintext,
        in_subject="Pine API Test Email",
        in_from="Pine API <{}>".format(smtp_username),
        in_htmltext=html,
    )

    # Set recipient
    sender.set_recipients([test_recipient])

    # Connect and send
    print(f"Connecting to {smtp_server}:{smtp_port}...")
    if sender.connect():
        print("Connection successful, sending email...")
        success_count = sender.send_all(close_connection=True)
        if success_count > 0:
            print(f"Email sent successfully to {test_recipient}")
        else:
            print("Failed to send email")
    else:
        print("Failed to connect to SMTP server")


def validate_config():
    """Validate the SMTP configuration"""
    print("Validating SMTP configuration...")
    load_dotenv()
    is_valid, message = validate_smtp_config()
    print(f"Configuration valid: {is_valid}")
    print(f"Message: {message}")

    if is_valid:
        print("\nTesting SMTP connection...")
        success, conn_message = test_smtp_connection()
        print(f"Connection successful: {success}")
        print(f"Message: {conn_message}")


if __name__ == "__main__":
    # First validate the configuration
    validate_config()

    # Ask user if they want to send a test email
    choice = input("\nDo you want to send a test email? (y/n): ")
    if choice.lower() == "y":
        test_mail_sender()
    else:
        print("Test email sending skipped.")
