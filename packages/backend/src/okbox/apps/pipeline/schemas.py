"""Pipeline file upload schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from okbox.apps.pipeline.models import UploadStatus


class UploadInitRequest(BaseModel):
    """Initiate a chunked upload."""

    filename: str = Field(..., min_length=1, max_length=500)
    file_size: int = Field(..., gt=0)
    sample_id: uuid.UUID
    content_type: str = "application/octet-stream"
    total_chunks: int = Field(1, ge=1)
    checksum_sha256: str | None = None


class UploadInitResponse(BaseModel):
    """Response after upload initiation."""

    upload_id: uuid.UUID
    object_path: str
    total_chunks: int


class ChunkUploadResponse(BaseModel):
    """Response after a chunk upload."""

    upload_id: uuid.UUID
    chunk_number: int
    uploaded_chunks: int
    total_chunks: int
    completed: bool


class UploadCompleteRequest(BaseModel):
    """Complete a chunked upload."""

    checksum_sha256: str | None = None


class FileRecordResponse(BaseModel):
    """File record response."""

    id: uuid.UUID
    filename: str
    object_path: str
    content_type: str
    file_size: int
    checksum_sha256: str | None
    upload_status: UploadStatus
    sample_id: uuid.UUID | None
    total_chunks: int
    uploaded_chunks: int
    created_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True


class UploadProgressResponse(BaseModel):
    """Upload progress information."""

    upload_id: uuid.UUID
    filename: str
    file_size: int
    uploaded_chunks: int
    total_chunks: int
    status: UploadStatus
    progress_percent: float
