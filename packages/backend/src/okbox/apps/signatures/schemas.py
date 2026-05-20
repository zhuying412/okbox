"""Signature schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from okbox.apps.signatures.models import SignatureRole, SignatureStatus


class SignRequest(BaseModel):
    """Sign a report."""

    report_id: uuid.UUID
    signer_id: uuid.UUID
    role: SignatureRole
    signer_name: str = Field(..., min_length=1, max_length=100)
    signer_qualification: str | None = None
    password: str = Field(..., min_length=1)  # Second factor authentication


class SignatureResponse(BaseModel):
    """Signature response."""

    id: uuid.UUID
    report_id: uuid.UUID
    signer_id: uuid.UUID
    role: SignatureRole
    status: SignatureStatus
    signer_name: str
    signer_qualification: str | None
    content_hash: str
    signature_timestamp: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class VerifyResponse(BaseModel):
    """Signature verification result."""

    valid: bool
    message: str
