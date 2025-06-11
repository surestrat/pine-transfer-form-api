from typing import Optional

from pydantic import BaseModel, EmailStr
from app.utils.examples import get_transfer_example, get_transfer_response_example


class CustomerInfo(BaseModel):
    first_name: str
    last_name: str
    email:Optional[EmailStr] = None
    contact_number: str
    id_number: Optional[str] = None
    quote_id: Optional[str] = None


class AgentInfo(BaseModel):
    agent_name: str
    branch_name: str

class ExTransferRequest(BaseModel):
    customer_info: CustomerInfo
    model_config = {
        "extra": "allow",
        "validate_assignment": True,
    }

class InTransferRequest(BaseModel):
    customer_info: CustomerInfo
    agent_info: AgentInfo
    model_config = {
        "extra": "allow",
        "validate_assignment": True,
        "json_schema_extra": {"example": get_transfer_example()},
    }


class TransferResponse(BaseModel):
    uuid: str
    redirect_url: str
    model_config = {
        "extra": "allow",
        "validate_assignment": True,
        "json_schema_extra": {"example": get_transfer_response_example()},
    }
