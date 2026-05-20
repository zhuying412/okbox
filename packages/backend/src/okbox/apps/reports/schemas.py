"""Report schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from okbox.apps.reports.models import ReportStatus


class TemplateCreateRequest(BaseModel):
    """Create a report template."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    html_template: str = Field(..., min_length=1)


class TemplateResponse(BaseModel):
    """Report template response."""

    id: uuid.UUID
    name: str
    description: str | None
    html_template: str
    is_active: bool
    version: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReportGenerateRequest(BaseModel):
    """Generate a report for a sample."""

    sample_id: uuid.UUID
    template_id: uuid.UUID
    title: str = Field(..., min_length=1, max_length=200)


class ReportResponse(BaseModel):
    """Generated report response."""

    id: uuid.UUID
    sample_id: uuid.UUID
    template_id: uuid.UUID
    title: str
    status: ReportStatus
    version: int
    pdf_path: str | None
    created_at: datetime
    generated_at: datetime | None

    class Config:
        from_attributes = True
