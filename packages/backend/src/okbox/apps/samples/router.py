"""Sample API routes."""

import uuid

from fastapi import APIRouter, Depends, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from okbox.apps.samples.models import SampleStatus, SampleType
from okbox.apps.samples.schemas import (
    BatchImportResult,
    SampleCreateRequest,
    SampleListQuery,
    SampleResponse,
    SampleUpdateRequest,
)
from okbox.apps.samples.service import (
    batch_import_samples,
    create_sample,
    get_sample,
    list_samples,
    update_sample,
)
from okbox.core.database import get_db

router = APIRouter(prefix="/samples", tags=["samples"])


@router.post("", response_model=SampleResponse, status_code=201)
async def create_sample_endpoint(
    request: SampleCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> SampleResponse:
    """Register a new sample."""
    sample = await create_sample(db, request)
    return SampleResponse.model_validate(sample)


@router.get("", response_model=dict)
async def list_samples_endpoint(
    status: SampleStatus | None = Query(None),
    sample_type: SampleType | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List samples with pagination and filters."""
    query = SampleListQuery(
        status=status, sample_type=sample_type, search=search, page=page, page_size=page_size
    )
    samples, total = await list_samples(db, query)
    return {
        "items": [SampleResponse.model_validate(s) for s in samples],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{sample_id}", response_model=SampleResponse)
async def get_sample_endpoint(
    sample_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SampleResponse:
    """Get sample details."""
    sample = await get_sample(db, sample_id)
    return SampleResponse.model_validate(sample)


@router.patch("/{sample_id}", response_model=SampleResponse)
async def update_sample_endpoint(
    sample_id: uuid.UUID,
    request: SampleUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> SampleResponse:
    """Update a sample."""
    sample = await update_sample(db, sample_id, request)
    return SampleResponse.model_validate(sample)


@router.post("/import", response_model=BatchImportResult)
async def import_samples_endpoint(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
) -> BatchImportResult:
    """Batch import samples from CSV/Excel file."""
    content = await file.read()
    csv_content = content.decode("utf-8")
    return await batch_import_samples(db, csv_content)
