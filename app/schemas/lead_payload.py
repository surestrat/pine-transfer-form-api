from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class LeadPayload(BaseModel):
    source: str = Field(..., min_length=2)
    first_name: str = Field(..., min_length=2)
    last_name: str = Field(..., min_length=2)
    email: EmailStr
    id_number: Optional[str] = Field(None, min_length=13)
    quote_id: Optional[str] = None
    contact_number: str = Field(..., min_length=10)
    additionalProp1: Optional[dict] = None