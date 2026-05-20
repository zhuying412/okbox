"""Clinical interpretation schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from okbox.apps.variants.interpretation_models import InterpretationStatus, Pathogenicity


class InterpretationCreateRequest(BaseModel):
    """Create an interpretation."""

    variant_id: uuid.UUID
    sample_id: uuid.UUID
    pathogenicity: Pathogenicity
    include_in_report: bool = False
    notes: str | None = None
    evidence: str | None = None
    interpreted_by: uuid.UUID | None = None


class InterpretationUpdateRequest(BaseModel):
    """Update an interpretation."""

    pathogenicity: Pathogenicity | None = None
    include_in_report: bool | None = None
    notes: str | None = None
    evidence: str | None = None


class InterpretationReviewRequest(BaseModel):
    """Review an interpretation."""

    reviewed_by: uuid.UUID
    notes: str | None = None


class InterpretationResponse(BaseModel):
    """Interpretation response."""

    id: uuid.UUID
    variant_id: uuid.UUID
    sample_id: uuid.UUID
    pathogenicity: Pathogenicity
    include_in_report: bool
    notes: str | None
    evidence: str | None
    status: InterpretationStatus
    interpreted_by: uuid.UUID | None
    reviewed_by: uuid.UUID | None
    interpreted_at: datetime | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InterpretationHistoryResponse(BaseModel):
    """Interpretation history response."""

    id: uuid.UUID
    interpretation_id: uuid.UUID
    variant_id: uuid.UUID
    action: str
    old_pathogenicity: str | None
    new_pathogenicity: str | None
    old_status: str | None
    new_status: str | None
    notes: str | None
    user_id: uuid.UUID
    username: str | None
    created_at: datetime

    class Config:
        from_attributes = True
