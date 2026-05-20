"""Sample business logic."""

import csv
import io
import uuid
from datetime import datetime

from sqlalchemy import func as sa_func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from okbox.apps.samples.models import Sample, SampleStatus, SampleType
from okbox.apps.samples.schemas import (
    BatchImportResult,
    SampleCreateRequest,
    SampleListQuery,
    SampleUpdateRequest,
)
from okbox.core.exceptions import NotFoundException, ValidationException

# Valid status transitions
VALID_TRANSITIONS: dict[SampleStatus, list[SampleStatus]] = {
    SampleStatus.REGISTERED: [SampleStatus.ANALYZING],
    SampleStatus.ANALYZING: [SampleStatus.INTERPRETED],
    SampleStatus.INTERPRETED: [SampleStatus.REPORTED],
    SampleStatus.REPORTED: [SampleStatus.SIGNED],
    SampleStatus.SIGNED: [],
}


async def create_sample(
    db: AsyncSession, request: SampleCreateRequest, user_id: uuid.UUID | None = None
) -> Sample:
    """Create a new sample."""
    # Check uniqueness
    result = await db.execute(select(Sample).where(Sample.sample_no == request.sample_no))
    if result.scalar_one_or_none():
        raise ValidationException(f"Sample number '{request.sample_no}' already exists")

    sample = Sample(
        sample_no=request.sample_no,
        patient_name=request.patient_name,
        patient_id_number=request.patient_id_number,
        sample_type=request.sample_type,
        panel_type=request.panel_type,
        received_date=request.received_date,
        notes=request.notes,
        patient_id=request.patient_id,
        created_by=user_id,
    )
    db.add(sample)
    await db.flush()
    await db.refresh(sample)
    return sample


async def get_sample(db: AsyncSession, sample_id: uuid.UUID) -> Sample:
    """Get a sample by ID."""
    result = await db.execute(select(Sample).where(Sample.id == sample_id))
    sample = result.scalar_one_or_none()
    if not sample:
        raise NotFoundException("Sample not found")
    return sample


async def update_sample(
    db: AsyncSession, sample_id: uuid.UUID, request: SampleUpdateRequest
) -> Sample:
    """Update a sample."""
    sample = await get_sample(db, sample_id)

    # Validate status transition
    if request.status and request.status != sample.status:
        if request.status not in VALID_TRANSITIONS.get(sample.status, []):
            raise ValidationException(
                f"Invalid status transition: {sample.status.value} -> {request.status.value}"
            )

    # Apply updates
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(sample, key, value)

    await db.flush()
    await db.refresh(sample)
    return sample


async def list_samples(
    db: AsyncSession, query: SampleListQuery
) -> tuple[list[Sample], int]:
    """List samples with filters and pagination."""
    stmt = select(Sample)
    count_stmt = select(sa_func.count(Sample.id))

    if query.status:
        stmt = stmt.where(Sample.status == query.status)
        count_stmt = count_stmt.where(Sample.status == query.status)
    if query.sample_type:
        stmt = stmt.where(Sample.sample_type == query.sample_type)
        count_stmt = count_stmt.where(Sample.sample_type == query.sample_type)
    if query.search:
        search_filter = or_(
            Sample.sample_no.ilike(f"%{query.search}%"),
            Sample.patient_name.ilike(f"%{query.search}%"),
        )
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    offset = (query.page - 1) * query.page_size
    stmt = stmt.order_by(Sample.created_at.desc()).offset(offset).limit(query.page_size)

    result = await db.execute(stmt)
    samples = list(result.scalars().all())

    return samples, total


async def batch_import_samples(
    db: AsyncSession, csv_content: str, user_id: uuid.UUID | None = None
) -> BatchImportResult:
    """Import samples from CSV content."""
    reader = csv.DictReader(io.StringIO(csv_content))
    success_count = 0
    errors: list[str] = []

    for row_num, row in enumerate(reader, start=2):
        try:
            sample_no = row.get("sample_no", "").strip()
            if not sample_no:
                errors.append(f"Row {row_num}: missing sample_no")
                continue

            # Check if already exists
            result = await db.execute(select(Sample).where(Sample.sample_no == sample_no))
            if result.scalar_one_or_none():
                errors.append(f"Row {row_num}: sample_no '{sample_no}' already exists")
                continue

            sample = Sample(
                sample_no=sample_no,
                patient_name=row.get("patient_name", "").strip() or None,
                sample_type=SampleType(row.get("sample_type", "other").strip()),
                panel_type=row.get("panel_type", "").strip() or "default",
                received_date=datetime.strptime(
                    row.get("received_date", "").strip(), "%Y-%m-%d"
                ).date(),
                created_by=user_id,
            )
            db.add(sample)
            success_count += 1
        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")

    if success_count > 0:
        await db.flush()

    return BatchImportResult(
        success_count=success_count,
        error_count=len(errors),
        errors=errors[:20],  # Limit error messages
    )
