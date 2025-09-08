#!/usr/bin/env python3
"""
Test API endpoints to verify email notifications are triggered
"""

import requests
import json
import time
import sys

def test_quote_api():
    """Test quote API endpoint and check if email notification is triggered"""
    print("=== Testing Quote API Email Notifications ===")
    
    url = "http://localhost:4000/api/v1/quote"
    
    # Sample quote request matching the schema
    quote_data = {
        "source": "SureStrat",
        "externalReferenceId": f"TEST-EMAIL-{int(time.time())}",
        "agentEmail": "test@surestrat.co.za",
        "agentBranch": "Test Branch",
        "vehicles": [
            {
                "year": 2020,
                "make": "Toyota",
                "model": "Corolla",
                "retailValue": 250000,  # Added missing field
                "marketValue": 220000,
                "address": {
                    "addressLine": "123 Test Street",
                    "postalCode": 7700,
                    "suburb": "Test Suburb"
                },
                "regularDriver": {
                    "maritalStatus": "Single",
                    "currentlyInsured": True,
                    "yearsWithoutClaims": 5,
                    "relationToPolicyHolder": "Self",
                    "emailAddress": "driver@example.com",
                    "mobileNumber": "0712345678",
                    "idNumber": "9001011234567",
                    "dateOfBirth": "1990-01-01",
                    "licenseIssueDate": "2008-01-01"  # Added missing field
                }
            }
        ]
    }
    
    try:
        print("🔄 Sending quote request...")
        print(f"URL: {url}")
        print(f"Data: {json.dumps(quote_data, indent=2)}")
        
        response = requests.post(url, json=quote_data, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Quote API request successful")
            print("💡 Check server logs for email notification status")
            return True
        else:
            print(f"❌ Quote API request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Quote API request exception: {e}")
        return False

def test_transfer_api():
    """Test transfer API endpoint and check if email notification is triggered"""
    print("\n=== Testing Transfer API Email Notifications ===")
    
    url = "http://localhost:4000/api/v1/transfer"
    
    # Sample transfer request matching the schema
    transfer_data = {
        "customer_info": {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "contact_number": f"07{int(time.time()) % 100000000}",  # Generate unique phone number
            "id_number": f"90010112345{int(time.time()) % 100}",  # Generate unique ID number
            "quote_id": "TEST-QUOTE-123"
        },
        "agent_info": {
            "agent_email": "test@surestrat.co.za",
            "branch_name": "Test Branch"
        }
    }
    
    try:
        print("🔄 Sending transfer request...")
        print(f"URL: {url}")
        print(f"Data: {json.dumps(transfer_data, indent=2)}")
        
        response = requests.post(url, json=transfer_data, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Transfer API request successful")
            print("💡 Check server logs for email notification status")
            return True
        else:
            print(f"❌ Transfer API request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Transfer API request exception: {e}")
        return False

if __name__ == "__main__":
    print("Testing API endpoints for email notifications...")
    print("Make sure the server is running on http://localhost:4000")
    print()
    
    # Test quote API
    quote_success = test_quote_api()
    
    # Wait a moment between tests
    time.sleep(2)
    
    # Test transfer API
    transfer_success = test_transfer_api()
    
    print("\n" + "="*50)
    if quote_success and transfer_success:
        print("🎉 All API tests completed successfully!")
        print("📧 Check your email and server logs for notifications")
    else:
        print(f"❌ Some tests failed - Quote: {quote_success}, Transfer: {transfer_success}")
    
    print("📊 Monitor server terminal for detailed email logs")
    sys.exit(0 if quote_success and transfer_success else 1)
