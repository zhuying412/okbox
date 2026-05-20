"""Patient API routes."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from okbox.apps.patients.models import Patient
from okbox.apps.patients.schemas import (
    PatientCreateRequest,
    PatientResponse,
    PatientUpdateRequest,
)
from okbox.core.database import get_db
from okbox.core.exceptions import NotFoundException, ValidationException

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=PatientResponse, status_code=201)
async def create_patient(
    request: PatientCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> PatientResponse:
    """Create a new patient."""
    # Check uniqueness
    result = await db.execute(
        select(Patient).where(Patient.patient_no == request.patient_no)
    )
    if result.scalar_one_or_none():
        raise ValidationException(f"Patient no '{request.patient_no}' already exists")

    patient = Patient(**request.model_dump())
    db.add(patient)
    await db.flush()
    await db.refresh(patient)
    return PatientResponse.from_model_desensitized(patient)


@router.get("", response_model=dict)
async def list_patients(
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List patients (desensitized) with search."""
    stmt = select(Patient)
    count_stmt = select(sa_func.count(Patient.id))

    if search:
        search_filter = or_(
            Patient.patient_no.ilike(f"%{search}%"),
            Patient.name.ilike(f"%{search}%"),
        )
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    stmt = stmt.order_by(Patient.created_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(stmt)
    patients = list(result.scalars().all())

    return {
        "items": [PatientResponse.from_model_desensitized(p) for p in patients],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> PatientResponse:
    """Get patient details (desensitized)."""
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise NotFoundException("Patient not found")
    return PatientResponse.from_model_desensitized(patient)


@router.patch("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: uuid.UUID,
    request: PatientUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> PatientResponse:
    """Update patient info."""
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise NotFoundException("Patient not found")

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(patient, key, value)

    await db.flush()
    await db.refresh(patient)
    return PatientResponse.from_model_desensitized(patient)


@router.get("/{patient_id}/samples", response_model=dict)
async def get_patient_samples(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get all samples for a patient (history timeline)."""
    from okbox.apps.samples.models import Sample

    result = await db.execute(
        select(Sample)
        .where(Sample.patient_id == patient_id)
        .order_by(Sample.created_at.desc())
    )
    samples = result.scalars().all()
    from okbox.apps.samples.schemas import SampleResponse

    return {
        "items": [SampleResponse.model_validate(s) for s in samples],
        "total": len(list(samples)),
    }
