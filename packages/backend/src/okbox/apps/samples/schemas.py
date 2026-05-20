"""Sample request/response schemas."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from okbox.apps.samples.models import SampleStatus, SampleType


class SampleCreateRequest(BaseModel):
    """Create a new sample."""

    sample_no: str = Field(..., min_length=1, max_length=50)
    patient_name: str | None = None
    patient_id_number: str | None = None
    sample_type: SampleType
    panel_type: str = Field(..., min_length=1, max_length=100)
    received_date: date
    notes: str | None = None
    patient_id: uuid.UUID | None = None


class SampleUpdateRequest(BaseModel):
    """Update a sample."""

    patient_name: str | None = None
    patient_id_number: str | None = None
    sample_type: SampleType | None = None
    panel_type: str | None = None
    received_date: date | None = None
    notes: str | None = None
    status: SampleStatus | None = None


class SampleResponse(BaseModel):
    """Sample response with desensitized patient info."""

    id: uuid.UUID
    sample_no: str
    patient_name: str | None
    sample_type: SampleType
    panel_type: str
    status: SampleStatus
    received_date: date
    notes: str | None
    patient_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SampleListQuery(BaseModel):
    """Sample list query parameters."""

    status: SampleStatus | None = None
    sample_type: SampleType | None = None
    search: str | None = None
    page: int = 1
    page_size: int = 20


class BatchImportResult(BaseModel):
    """Result of batch import operation."""

    success_count: int
    error_count: int
    errors: list[str]
