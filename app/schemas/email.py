from typing import Optional, List
from pydantic import BaseModel, EmailStr

class EmailAttachment(BaseModel):
    path: str
    filename: str

class EmailNotification(BaseModel):
    subject: str
    body: Optional[str] = None
    recipients: List[EmailStr]
    cc: Optional[List[EmailStr]] = None
    bcc: Optional[List[EmailStr]] = None
    html_body: Optional[str] = None
    attachments: Optional[List[EmailAttachment]] = None
    template_name: Optional[str] = None
    template_context: Optional[dict] = None

    class Config:
        extra = "forbid"
        anystr_strip_whitespace = True
        use_enum_values = True

class TestEmailRequest(BaseModel):
    email: EmailStr

