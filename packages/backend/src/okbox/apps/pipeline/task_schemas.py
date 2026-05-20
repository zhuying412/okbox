"""Pipeline task schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from okbox.apps.pipeline.task_models import TaskStatus


class TaskSubmitRequest(BaseModel):
    """Submit a pipeline task."""

    sample_id: uuid.UUID
    pipeline_name: str = Field(..., min_length=1, max_length=100)
    pipeline_version: str = Field(..., min_length=1, max_length=50)
    inputs: dict | None = None
    parameters: dict | None = None
    max_retries: int = Field(3, ge=0, le=10)


class TaskResponse(BaseModel):
    """Pipeline task response."""

    id: uuid.UUID
    status: TaskStatus
    pipeline_name: str
    pipeline_version: str
    sample_id: uuid.UUID | None
    inputs: dict | None
    outputs: dict | None
    parameters: dict | None
    error_message: str | None
    retry_count: int
    max_retries: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    class Config:
        from_attributes = True


class TaskListQuery(BaseModel):
    """Task list query parameters."""

    status: TaskStatus | None = None
    sample_id: uuid.UUID | None = None
    pipeline_name: str | None = None
    page: int = 1
    page_size: int = 20


class TaskLogResponse(BaseModel):
    """Task execution log."""

    task_id: uuid.UUID
    log_content: str
    run_dir: str | None
