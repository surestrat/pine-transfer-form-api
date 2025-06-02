"""
Example payloads for API documentation and testing
"""

from typing import Dict, Any
import json


def get_quote_example() -> Dict[str, Any]:
    """
    Returns an example payload for the quick quote endpoint that matches the Postman collection.

    This is properly formatted with date strings in ISO format (YYYY-MM-DD)
    which JSON can handle without serialization issues.
    """
    return {
        "source": "SureStrat",  # Note: Case sensitive, must be "SureStrat" not "Surestrat"
        "externalReferenceId": "12345678910",  # Match Postman collection example
        "vehicles": [
            {
                "year": 2019,
                "make": "Volkswagen",
                "model": "Polo Tsi 1.2 Comfortline",
                "mmCode": "00815170",
                "modified": "N",
                "category": "HB",
                "colour": "White",
                "engineSize": 1.2,
                "financed": "N",
                "owner": "Y",
                "status": "New",
                "partyIsRegularDriver": "Y",
                "accessories": "Y",
                "accessoriesAmount": 20000,
                "retailValue": 200000,
                "marketValue": 180000,
                "insuredValueType": "Retail",
                "useType": "Private",
                "overnightParkingSituation": "Garage",
                "coverCode": "Comprehensive",
                "address": {
                    "addressLine": "123 Main Street",
                    "postalCode": 2196,
                    "suburb": "Sandton",
                    "latitude": -26.10757,
                    "longitude": 28.0567,
                },
                "regularDriver": {
                    "maritalStatus": "Married",
                    "currentlyInsured": True,
                    "yearsWithoutClaims": 0,
                    "relationToPolicyHolder": "Self",
                    "emailAddress": "example@gmail.com",
                    "mobileNumber": "0821234567",
                    "idNumber": "9404054800086",
                    "prvInsLosses": 0,
                    "licenseIssueDate": "2018-10-02",
                    "dateOfBirth": "1994-04-05",
                },
            }
        ],
    }


def get_transfer_example() -> Dict[str, Any]:
    """
    Returns an example payload for the transfer form endpoint that matches the Postman collection.

    Contains all necessary fields for a vehicle transfer request based on defined schemas.
    """
    return {
        "customer_info": {
            "first_name": "Peter",
            "last_name": "Smith",
            "email": "peterSmith007@pineapple.co.za",
            "contact_number": "0737111119",
            "id_number": "9510025800086",
            "quote_id": "67977c1c4130345e85bb7572",
            "source": "SureStrat",  # Note: Case sensitive, must be "SureStrat" not "Surestrat"
        },
        "agent_info": {
            "agent_name": "John Doe",
            "branch_name": "Sandton",
        },
    }


def get_transfer_response_example() -> Dict[str, Any]:
    """
    Returns an example response for the transfer form endpoint.

    Follows the ExTransferResponse schema for Swagger documentation.
    """
    return {
        "success": True,
        "data": {
            "uuid": "12345678-1234-5678-1234-567812345678",
            "redirect_url": "https://example.com/form/12345678-1234-5678-1234-567812345678",
        },
    }


def get_transfer_error_example() -> Dict[str, Any]:
    """
    Returns an example error response for the transfer form endpoint.

    Follows the ExTransferResponse schema with an error for Swagger documentation.
    """
    return {
        "success": False,
        "data": None,
        "error_message": "Failed to process transfer request: Invalid customer information",
        "message": "Transfer failed",
    }


def get_quote_response_example() -> Dict[str, Any]:
    """
    Returns an example successful response for the quote endpoint.

    Follows the ExQuoteResponse schema for Swagger documentation.
    """
    return {
        "success": True,
        "id": "12345678-1234-5678-1234-567812345678",
        "data": [
            {
            "premium": 1250.00,
            "excess": 5000,
            }
        ],
    }


def get_quote_error_example() -> Dict[str, Any]:
    """
    Returns an example error response for the quote endpoint.

    Follows the ExQuoteResponse schema with an error for Swagger documentation.
    """
    return {
        "success": False,
        "message": "Quote failed",
        "id": None,
        "data": None,
        "error_message": "Failed to generate quote: Vehicle not eligible for coverage",
    }


def get_quote_json_string_example() -> str:
    """Returns the quick quote example as a properly formatted JSON string"""
    return json.dumps(get_quote_example())


def get_transfer_json_string_example() -> str:
    """Returns the transfer example as a properly formatted JSON string"""
    return json.dumps(get_transfer_example())
