#!/usr/bin/env python3
"""
Test transfer email template functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.email import EmailService
from app.schemas.transfer import InTransferRequest, CustomerInfo, AgentInfo
from config.settings import settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_transfer_email():
    """Test transfer notification email with various scenarios"""
    print("=== Transfer Email Test ===")
    
    email_service = EmailService()
    
    # Test case 1: Complete transfer data
    complete_transfer = InTransferRequest(
        customer_info=CustomerInfo(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            contact_number="0712345678",
            id_number="9001011234567",
            quote_id="QUOTE-123456"
        ),
        agent_info=AgentInfo(
            agent_email="agent@surestrat.co.za",
            branch_name="Cape Town Branch"
        )
    )
    
    # Test case 2: Missing optional fields
    minimal_transfer = InTransferRequest(
        customer_info=CustomerInfo(
            first_name="Jane",
            last_name="Smith",
            email=None,  # Optional field
            contact_number="0723456789",
            id_number=None,  # Optional field
            quote_id=None   # Optional field
        ),
        agent_info=AgentInfo(
            agent_email="agent2@surestrat.co.za",
            branch_name="Johannesburg Branch"
        )
    )
    
    test_cases = [
        ("Complete Transfer", complete_transfer, True, None),
        ("Minimal Transfer", minimal_transfer, True, None),
        ("Failed Transfer", complete_transfer, False, "API connection timeout"),
    ]
    
    all_passed = True
    
    for test_name, transfer_data, success, error_message in test_cases:
        try:
            print(f"\n🔄 Testing: {test_name}")
            
            # Test sending the actual email
            result = email_service.send_email(
                subject=f"[TEST] Lead Transfer {'Success' if success else 'Failed'}: {transfer_data.customer_info.first_name} {transfer_data.customer_info.last_name}",
                recipients=settings.ADMIN_EMAILS,
                template_name="transfer_notification.html",
                template_context={
                    "transfer": transfer_data,
                    "status_line": "✅ New Report" if success else f"❌ Lead transfer failed: {error_message}",
                    "success": success,
                    "error_message": error_message
                },
                bcc=settings.ADMIN_BCC_EMAILS if hasattr(settings, 'ADMIN_BCC_EMAILS') and settings.ADMIN_BCC_EMAILS else None
            )
            
            if result:
                print(f"✅ {test_name}: Email sent successfully")
            else:
                print(f"❌ {test_name}: Email failed to send")
                all_passed = False
                
        except Exception as e:
            print(f"❌ {test_name}: Exception occurred - {e}")
            all_passed = False
    
    return all_passed

def test_transfer_template_only():
    """Test just template rendering without sending emails"""
    print("\n=== Transfer Template Rendering Test ===")
    
    email_service = EmailService()
    
    # Test with minimal data to check robustness
    minimal_transfer = InTransferRequest(
        customer_info=CustomerInfo(
            first_name="Test",
            last_name="User",
            contact_number="0700000000"
        ),
        agent_info=AgentInfo(
            agent_email="test@surestrat.co.za",
            branch_name="Test Branch"
        )
    )
    
    try:
        rendered = email_service.render_template("transfer_notification.html", {
            "transfer": minimal_transfer,
            "status_line": "✅ New Report",
            "success": True,
            "error_message": None
        })
        
        if "An error occurred while rendering the email template" in rendered:
            print("❌ Template rendering failed")
            return False
        else:
            print(f"✅ Template rendered successfully ({len(rendered)} chars)")
            return True
            
    except Exception as e:
        print(f"❌ Template rendering exception: {e}")
        return False

if __name__ == "__main__":
    # Test template rendering first
    template_success = test_transfer_template_only()
    
    # Test full email functionality
    email_success = test_transfer_email()
    
    if template_success and email_success:
        print("\n🎉 All transfer email tests passed!")
        sys.exit(0)
    else:
        print(f"\n❌ Transfer email tests failed - Template: {template_success}, Email: {email_success}")
        sys.exit(1)
