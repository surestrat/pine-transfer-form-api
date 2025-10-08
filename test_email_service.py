#!/usr/bin/env python3
"""
Test script to verify email sending functionality
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from app.services.email import EmailService
from app.schemas.transfer import InTransferRequest, CustomerInfo, AgentInfo

def test_email_configuration():
    """Test email configuration"""
    print("📧 Testing Email Configuration...")
    print(f"SMTP Server: {settings.SMTP_SERVER}")
    print(f"SMTP Port: {settings.SMTP_PORT}")
    print(f"SMTP Username: {settings.SMTP_USERNAME}")
    print(f"SMTP Password: {'*' * len(settings.SMTP_PASSWORD) if settings.SMTP_PASSWORD else 'NOT SET'}")
    print(f"Email From: {settings.EMAIL_FROM}")
    print(f"Admin Emails: {settings.ADMIN_EMAILS}")
    print(f"Send Transfer Notifications: {settings.SEND_TRANSFER_NOTIFICATIONS}")
    print(f"Send Quote Notifications: {settings.SEND_QUOTE_NOTIFICATIONS}")

def test_smtp_connection():
    """Test SMTP connection"""
    print("\n🔗 Testing SMTP Connection...")
    try:
        import smtplib
        import ssl
        
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT, context=context) as server:
            print("✅ SMTP SSL connection successful")
            
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                try:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                    print("✅ SMTP authentication successful")
                    return True
                except Exception as e:
                    print(f"❌ SMTP authentication failed: {e}")
                    return False
            else:
                print("❌ SMTP credentials not configured")
                return False
    except Exception as e:
        print(f"❌ SMTP connection failed: {e}")
        return False

def test_email_service():
    """Test EmailService class"""
    print("\n📨 Testing EmailService...")
    try:
        email_service = EmailService()
        print("✅ EmailService initialized successfully")
        return email_service
    except Exception as e:
        print(f"❌ EmailService initialization failed: {e}")
        return None

def test_send_simple_email(email_service):
    """Test sending a simple email"""
    print("\n📤 Testing Simple Email Send...")
    
    if not email_service:
        print("❌ EmailService not available")
        return False
    
    try:
        success = email_service.send_email(
            subject="Test Email - Supabase Migration",
            recipients=settings.ADMIN_EMAILS,
            template_name="transfer_notification.html",
            template_context={
                "transfer": {
                    "customer_info": {
                        "first_name": "Test",
                        "last_name": "User",
                        "email": "test@example.com",
                        "contact_number": "0123456789",
                        "id_number": "9001015009087"
                    },
                    "agent_info": {
                        "agent_email": "test.agent@surestrat.co.za",
                        "branch_name": "Test Branch"
                    }
                },
                "status_line": "✅ Test Email - Migration Complete",
                "success": True,
                "error_message": None
            }
        )
        
        if success:
            print("✅ Email sent successfully")
            return True
        else:
            print("❌ Email sending failed")
            return False
    except Exception as e:
        print(f"❌ Email sending error: {e}")
        return False

def test_transfer_email(email_service):
    """Test sending a transfer email"""
    print("\n📋 Testing Transfer Email...")
    
    if not email_service:
        print("❌ EmailService not available")
        return False
    
    try:
        # Create test transfer data
        customer_info = CustomerInfo(
            first_name="Test",
            last_name="Customer",
            email="test.customer@example.com",
            contact_number="0123456789",
            id_number="9001015009087",
            quote_id="TEST-001"
        )
        
        agent_info = AgentInfo(
            agent_email="test.agent@surestrat.co.za",
            branch_name="Test Branch"
        )
        
        transfer_data = InTransferRequest(
            customer_info=customer_info,
            agent_info=agent_info
        )
        
        # Test the transfer email function
        import asyncio
        success = asyncio.run(email_service.send_transfer_email(
            recipient=settings.ADMIN_EMAILS,
            transfer_data=transfer_data,
            success=True,
            error_message=None,
            cc=None,
            bcc=None
        ))
        
        if success:
            print("✅ Transfer email sent successfully")
            return True
        else:
            print("❌ Transfer email sending failed")
            return False
    except Exception as e:
        print(f"❌ Transfer email error: {e}")
        return False

def main():
    print("🚀 Email Service Test")
    print("=" * 50)
    
    # Test configuration
    test_email_configuration()
    
    # Test SMTP connection
    smtp_ok = test_smtp_connection()
    if not smtp_ok:
        print("\n❌ SMTP connection failed - check your email settings")
        return
    
    # Test EmailService
    email_service = test_email_service()
    
    # Test simple email
    simple_ok = test_send_simple_email(email_service)
    
    # Test transfer email
    transfer_ok = test_transfer_email(email_service)
    
    print("\n" + "=" * 50)
    print(f"📊 Results:")
    print(f"   SMTP Connection: {'✅' if smtp_ok else '❌'}")
    print(f"   Simple Email: {'✅' if simple_ok else '❌'}")
    print(f"   Transfer Email: {'✅' if transfer_ok else '❌'}")
    
    if all([smtp_ok, simple_ok, transfer_ok]):
        print("🎉 All email tests passed!")
    else:
        print("⚠️  Some email tests failed - check the logs above")

if __name__ == "__main__":
    main()