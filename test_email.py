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

from app.email_service import MailSender, send_email
from app.email_validation import validate_smtp_config, test_smtp_connection
from app.schemas import AdminNotification


def test_mail_sender():
    """Test the MailSender class directly"""
    print("Testing MailSender class...")

    # Get SMTP settings from environment variables
    load_dotenv()
    smtp_username = os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS")
    smtp_server = os.getenv("SMTP_SERVER") or os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT") or 465)

    print(f"SMTP Server: {smtp_server}")
    print(f"SMTP Port: {smtp_port}")
    print(f"SMTP Username: {smtp_username}")
    print(f"SMTP Password: {'*' * len(smtp_password) if smtp_password else 'Not set'}")

    # Determine connection method based on port
    use_ssl = smtp_port in (465, 993)
    conn_method = "SSL" if use_ssl else "STARTTLS"
    print(f"Connection method: {conn_method}")

    # Get test recipient
    test_recipient = input(
        "Enter test recipient email (separate multiple emails with commas): "
    )

    # Parse multiple email addresses if provided
    recipients = [email.strip() for email in test_recipient.split(",") if email.strip()]
    if not recipients:
        print("No valid email addresses provided")
        return

    print(f"Will send to: {recipients}")

    # Check if SMTP server is configured
    if not smtp_server:
        print("Error: SMTP server not configured in environment variables")
        return

    # Create MailSender instance
    sender = MailSender(
        in_username=smtp_username,
        in_password=smtp_password,
        in_server=(smtp_server, smtp_port),
        use_SSL=use_ssl,  # Use SSL based on port detection
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
        in_from=f"Pine API <{smtp_username}>",
        in_htmltext=html,
    )

    # Set recipient(s)
    sender.set_recipients(recipients)

    # Connect and send
    print(f"Connecting to {smtp_server}:{smtp_port} using {conn_method}...")
    if sender.connect():
        print("Connection successful, sending email...")
        success_count = sender.send_all(close_connection=True)
        if success_count > 0:
            print(f"Email sent successfully to {recipients}")
        else:
            print("Failed to send email")
    else:
        print("Failed to connect to SMTP server")


def test_send_email_function():
    """Test the actual send_email function used by the API"""
    print("Testing send_email function...")

    # Get test recipient
    test_recipient = input(
        "Enter test recipient email (separate multiple emails with commas): "
    )

    # Parse multiple email addresses
    recipients = [email.strip() for email in test_recipient.split(",") if email.strip()]
    if not recipients:
        print("No valid email addresses provided")
        return

    print(f"Will send to: {recipients}")

    # Create notification
    notification = AdminNotification(
        subject="Test Email via send_email function",
        body="This is a test email using the API's send_email function.",
        html_body="""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #0056b3;">Send Email Function Test</h2>
            <p>This email was sent using the API's send_email function.</p>
            <p>If you're seeing this, the function is working correctly!</p>
        </body>
        </html>
        """,
        recipients=recipients,  # Pass the list of individual emails, not the comma-separated string
    )

    # Send the email
    print("Sending email...")
    result = send_email(notification)

    if result:
        print(f"Email sent successfully to {recipients}")
    else:
        print("Failed to send email")


def validate_config():
    """Validate the SMTP configuration"""
    print("Validating SMTP configuration...")
    load_dotenv()

    # Print out the SMTP settings for verification
    smtp_username = os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER")
    smtp_server = os.getenv("SMTP_SERVER") or os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT") or "465"

    print(f"SMTP Server: {smtp_server}")
    print(f"SMTP Port: {smtp_port}")
    print(f"SMTP Username: {smtp_username}")

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

    # Ask user which test to run
    print("\nChoose a test to run:")
    print("1. Test MailSender class directly")
    print("2. Test send_email function (used by the API)")
    print("3. Run both tests")
    print("4. Skip tests")

    choice = input("Enter choice (1-4): ")

    if choice == "1":
        test_mail_sender()
    elif choice == "2":
        test_send_email_function()
    elif choice == "3":
        test_mail_sender()
        print("\n" + "-" * 50 + "\n")
        test_send_email_function()
    else:
        print("Tests skipped.")
