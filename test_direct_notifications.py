#!/usr/bin/env python3
"""
Test email notifications by directly calling the background task functions
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.email import EmailService
from app.schemas.quote import QuoteRequest, Vehicle, Address, RegularDriver
from app.schemas.transfer import InTransferRequest, CustomerInfo, AgentInfo
from config.settings import settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

async def test_quote_notification():
    """Test quote notification email function directly"""
    print("=== Direct Quote Notification Test ===")
    
    email_service = EmailService()
    
    # Create a sample quote request
    quote = QuoteRequest(
        source="SureStrat",
        externalReferenceId="TEST-DIRECT-QUOTE-123",
        agentEmail="test@surestrat.co.za",
        agentBranch="Test Branch",
        vehicles=[
            Vehicle(
                year=2020,
                make="Toyota",
                model="Corolla",
                retailValue=250000,
                address=Address(
                    addressLine="123 Test Street",
                    postalCode=7700,
                    suburb="Test Suburb"
                ),
                regularDriver=RegularDriver(
                    maritalStatus="Single",
                    currentlyInsured=True,
                    yearsWithoutClaims=5,
                    relationToPolicyHolder="Self",
                    emailAddress="driver@example.com",
                    mobileNumber="0712345678",
                    idNumber="9001011234567",
                    dateOfBirth="1990-01-01",
                    licenseIssueDate="2008-01-01"
                )
            )
        ]
    )
    
    try:
        # Test the exact same function call as in the quote endpoint
        success = email_service.send_email(
            recipients=settings.ADMIN_EMAILS,
            subject="[DIRECT TEST] New Quote Request Received",
            template_name="quote_notification.html",
            template_context={
                "quote": quote.model_dump(mode="json"),
                "quote_response": {
                    "premium": 1200.50,
                    "excess": 5000,
                    "quoteId": "test-quote-id"
                }
            },
            cc="test@surestrat.co.za",
            bcc=settings.ADMIN_BCC_EMAILS if hasattr(settings, 'ADMIN_BCC_EMAILS') and settings.ADMIN_BCC_EMAILS else None
        )
        
        if success:
            print("✅ Quote notification sent successfully!")
            return True
        else:
            print("❌ Quote notification failed to send")
            return False
            
    except Exception as e:
        print(f"❌ Quote notification exception: {e}")
        return False

async def test_transfer_notification():
    """Test transfer notification email function directly"""
    print("\n=== Direct Transfer Notification Test ===")
    
    email_service = EmailService()
    
    # Create a sample transfer request
    transfer = InTransferRequest(
        customer_info=CustomerInfo(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            contact_number="0798765432",
            id_number="8805051234567",
            quote_id="QUOTE-TEST-456"
        ),
        agent_info=AgentInfo(
            agent_email="agent@surestrat.co.za",
            branch_name="Cape Town Branch"
        )
    )
    
    try:
        # Test the exact same function call as in the transfer endpoint
        success = await email_service.send_transfer_email(
            recipient=settings.ADMIN_EMAILS,
            transfer_data=transfer,
            success=True,
            error_message=None,
            cc="agent@surestrat.co.za",
            bcc=settings.ADMIN_BCC_EMAILS if hasattr(settings, 'ADMIN_BCC_EMAILS') and settings.ADMIN_BCC_EMAILS else None
        )
        
        if success:
            print("✅ Transfer notification sent successfully!")
            return True
        else:
            print("❌ Transfer notification failed to send")
            return False
            
    except Exception as e:
        print(f"❌ Transfer notification exception: {e}")
        return False

async def main():
    """Run all direct notification tests"""
    print("Testing email notifications directly...")
    print(f"Admin emails: {settings.ADMIN_EMAILS}")
    print(f"Admin BCC emails: {getattr(settings, 'ADMIN_BCC_EMAILS', 'Not set')}")
    print(f"Send quote notifications: {settings.SEND_QUOTE_NOTIFICATIONS}")
    print(f"Send transfer notifications: {settings.SEND_TRANSFER_NOTIFICATIONS}")
    print()
    
    quote_success = await test_quote_notification()
    transfer_success = await test_transfer_notification()
    
    print("\n" + "="*50)
    if quote_success and transfer_success:
        print("🎉 All direct notification tests passed!")
        print("📧 Check your email inbox and spam folder")
    else:
        print(f"❌ Some tests failed - Quote: {quote_success}, Transfer: {transfer_success}")
    
    return quote_success and transfer_success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
