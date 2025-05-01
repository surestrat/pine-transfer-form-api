from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class FormData(BaseModel):
    first_name: str = Field(..., min_length=2)
    last_name: str = Field(..., min_length=2)
    email: EmailStr
    id_number: Optional[str] = Field(None, min_length=13)
    quote_id: Optional[str] = None
    contact_number: str = Field(..., min_length=10)


class ExternalApiResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


class AgentInfo(BaseModel):
    agent: str = Field(..., min_length=2)
    branch: str = Field(..., min_length=2)


class SubmissionData(BaseModel):
    formData: FormData
    agentInfo: AgentInfo


class AdminNotification(BaseModel):
    subject: str
    body: str
    recipients: List[EmailStr]
