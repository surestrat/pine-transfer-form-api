#!/usr/bin/env python3
"""
Simple email test script to verify SMTP configuration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.email import EmailService
from config.settings import settings
import logging

# Set up logging to see detailed output
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_quote_email():
    """Test quote notification email specifically"""
    print("\n=== Quote Email Test ===")
    
    try:
        email_service = EmailService()
        
        # Test quote notification template context
        test_quote_context = {
            "quote": {
                "externalReferenceId": "TEST-QUOTE-123",
                "source": "SureStrat",
                "agentEmail": "test@surestrat.co.za",
                "agentBranch": "Test Branch",
                "vehicles": [
                    {
                        "make": "Toyota",
                        "model": "Corolla",
                        "year": 2020,
                        "registrationNumber": "ABC123GP"
                    }
                ]
            },
            "quote_response": {
                "premium": 1200.50,
                "excess": 5000,
                "quoteId": "quote-test-123"
            }
        }
        
        print("🔄 Testing quote notification email...")
        success = email_service.send_email(
            subject="[TEST] New Quote Request Received",
            recipients=settings.ADMIN_EMAILS,
            template_name="quote_notification.html",
            template_context=test_quote_context,
            bcc=settings.ADMIN_BCC_EMAILS if hasattr(settings, 'ADMIN_BCC_EMAILS') and settings.ADMIN_BCC_EMAILS else None
        )
        
        if success:
            print("✅ Quote notification email sent successfully!")
            print(f"   Recipients: {settings.ADMIN_EMAILS}")
            if hasattr(settings, 'ADMIN_BCC_EMAILS') and settings.ADMIN_BCC_EMAILS:
                print(f"   BCC: {settings.ADMIN_BCC_EMAILS}")
            return True
        else:
            print("❌ Quote notification email failed to send")
            return False
            
    except Exception as e:
        print(f"❌ Quote email test failed with exception: {e}")
        return False

def test_email_config():
    """Test email configuration and sending"""
    print("=== Email Configuration Test ===")
    
    # Print current settings
    print(f"SMTP Server: {settings.SMTP_SERVER}")
    print(f"SMTP Port: {settings.SMTP_PORT}")
    print(f"SMTP Username: {settings.SMTP_USERNAME}")
    print(f"SMTP Password: {'***' if settings.SMTP_PASSWORD else 'NOT SET'}")
    print(f"Email From: {settings.EMAIL_FROM}")
    print(f"Admin Emails: {settings.ADMIN_EMAILS}")
    print()
    
    # Initialize email service
    try:
        email_service = EmailService()
        print("✅ EmailService initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize EmailService: {e}")
        return False
    
    # Test template rendering
    try:
        test_context = {
            "test_message": "This is a test email to verify SMTP configuration.",
            "recipient": settings.ADMIN_EMAILS
        }
        
        # Create a simple test template
        test_template = """
        <html>
        <body>
            <h2>Email Test</h2>
            <p>{{ test_message }}</p>
            <p>Recipient: {{ recipient }}</p>
            <p>Timestamp: {{ now }}</p>
        </body>
        </html>
        """
        
        # Save test template
        with open("templates/test_email.html", "w") as f:
            f.write(test_template)
        
        rendered = email_service.render_template("test_email.html", test_context)
        print("✅ Template rendering works")
    except Exception as e:
        print(f"❌ Template rendering failed: {e}")
        return False
    
    # Test email sending
    try:
        print("🔄 Attempting to send test email...")
        success = email_service.send_email(
            subject="[TEST] Email Configuration Test",
            recipients=settings.ADMIN_EMAILS,
            template_name="test_email.html",
            template_context=test_context
        )
        
        if success:
            print("✅ Test email sent successfully!")
            return True
        else:
            print("❌ Test email failed to send")
            return False
            
    except Exception as e:
        print(f"❌ Email sending failed with exception: {e}")
        return False
    finally:
        # Clean up test template
        if os.path.exists("templates/test_email.html"):
            os.remove("templates/test_email.html")

if __name__ == "__main__":
    # Test basic email config first
    basic_success = test_email_config()
    
    # Test quote-specific email
    quote_success = test_quote_email()
    
    if basic_success and quote_success:
        print("\n🎉 All email tests passed!")
        sys.exit(0)
    else:
        print(f"\n❌ Email tests failed - Basic: {basic_success}, Quote: {quote_success}")
        sys.exit(1)
