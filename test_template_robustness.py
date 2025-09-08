#!/usr/bin/env python3
"""
Test email template with incomplete data to verify robustness
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.email import EmailService
from config.settings import settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_template_with_missing_data():
    """Test template rendering with various missing data scenarios"""
    print("=== Template Robustness Test ===")
    
    email_service = EmailService()
    
    # Test case 1: Complete data (should work perfectly)
    complete_data = {
        "quote": {
            "externalReferenceId": "TEST-COMPLETE-123",
            "source": "SureStrat",
            "agentEmail": "agent@surestrat.co.za",
            "agentBranch": "Test Branch",
            "vehicles": [
                {
                    "make": "Toyota",
                    "model": "Corolla",
                    "year": 2020,
                    "registrationNumber": "ABC123GP",
                    "regularDriver": {
                        "maritalStatus": "Single",
                        "currentlyInsured": True,
                        "yearsWithoutClaims": 5,
                        "emailAddress": "driver@example.com",
                        "mobileNumber": "0712345678",
                        "idNumber": "9001011234567",
                        "dateOfBirth": "1990-01-01"
                    },
                    "address": {
                        "addressLine": "123 Test Street",
                        "suburb": "Test Suburb",
                        "postalCode": 1234
                    }
                }
            ]
        },
        "quote_response": {
            "premium": 1200.50,
            "excess": 5000,
            "quoteId": "quote-complete-123"
        }
    }
    
    # Test case 2: Missing regularDriver (should show fallback)
    missing_driver_data = {
        "quote": {
            "externalReferenceId": "TEST-NO-DRIVER-123",
            "source": "SureStrat",
            "vehicles": [
                {
                    "make": "Honda",
                    "model": "Civic",
                    "year": 2019,
                    "address": {
                        "addressLine": "456 Test Avenue",
                        "suburb": "Test Town",
                        "postalCode": 5678
                    }
                }
            ]
        },
        "quote_response": {
            "premium": 950.00,
            "excess": 4000,
            "quoteId": "quote-no-driver-123"
        }
    }
    
    # Test case 3: Missing address (should show fallback)
    missing_address_data = {
        "quote": {
            "externalReferenceId": "TEST-NO-ADDRESS-123",
            "source": "SureStrat",
            "vehicles": [
                {
                    "make": "BMW",
                    "model": "3 Series",
                    "year": 2021,
                    "regularDriver": {
                        "maritalStatus": "Married",
                        "currentlyInsured": False,
                        "yearsWithoutClaims": 0
                    }
                }
            ]
        },
        "quote_response": {
            "premium": 1800.00,
            "excess": 7500,
            "quoteId": "quote-no-address-123"
        }
    }
    
    test_cases = [
        ("Complete Data", complete_data),
        ("Missing Driver", missing_driver_data),
        ("Missing Address", missing_address_data)
    ]
    
    all_passed = True
    
    for test_name, test_data in test_cases:
        try:
            print(f"\n🔄 Testing: {test_name}")
            
            # Test template rendering only (don't send actual emails)
            rendered = email_service.render_template("quote_notification.html", test_data)
            
            if "An error occurred while rendering the email template" in rendered:
                print(f"❌ {test_name}: Template rendering failed")
                all_passed = False
            else:
                print(f"✅ {test_name}: Template rendered successfully ({len(rendered)} chars)")
                
        except Exception as e:
            print(f"❌ {test_name}: Exception occurred - {e}")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    success = test_template_with_missing_data()
    if success:
        print("\n🎉 All template robustness tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some template tests failed")
        sys.exit(1)
