from pydantic import BaseModel, EmailStr, NonNegativeInt
from typing import Optional
from datetime import date
from app.utils.examples import get_quote_example, get_quote_response_example

class Address(BaseModel):
    addressLine: str
    postalCode: int  # changed from str to int
    suburb: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    model_config = {"extra": "allow"}

class RegularDriver(BaseModel):
    maritalStatus: str
    currentlyInsured: bool
    yearsWithoutClaims: NonNegativeInt
    relationToPolicyHolder: str
    emailAddress: Optional[EmailStr] = None
    mobileNumber: Optional[str] = None
    idNumber: Optional[str] = None
    prvInsLosses: Optional[NonNegativeInt] = None
    licenseIssueDate: Optional[str] = None
    dateOfBirth: Optional[date] = None

    model_config = {"extra":  "allow"}


class Vehicle(BaseModel):
    """Vehicle data for internal use"""

    year: int
    make: str
    model: str
    mmCode: Optional[str] = None
    modified: Optional[str] = None
    category: Optional[str] = None
    colour: Optional[str] = None
    engineSize: Optional[float] = None
    financed: Optional[str] = None
    owner: Optional[str] = None
    status: Optional[str] = None
    partyIsRegularDriver: Optional[str] = None
    accessories: Optional[str] = None
    accessoriesAmount: Optional[int] = None
    retailValue: Optional[int] = None
    marketValue: Optional[int] = None
    insuredValueType: Optional[str] = None
    useType: Optional[str] = None
    overnightParkingSituation: Optional[str] = None
    coverCode: Optional[str] = None

    address: Address
    regularDriver: RegularDriver

    model_config = {
        "validate_assignment": True,
        "arbitrary_types_allowed": True,
        "extra": "allow"
    }

class QuoteRequest(BaseModel):
    source: str
    externalReferenceId: str
    agentEmail: Optional[EmailStr] = None
    agentBranch: Optional[str] = None
    vehicles: list[Vehicle]
    model_config = {
        "extra": "allow",
        "validate_assignment": True,
        "json_schema_extra": {
            "example": get_quote_example()
        }
    }

class QuoteResponse(BaseModel):
    premium: float
    excess: float
    quoteId: Optional[str] = None
    model_config = {
        "extra": "allow",
        "validate_assignment": True,
        "json_schema_extra": {
            "example": get_quote_response_example()
        }
    }
