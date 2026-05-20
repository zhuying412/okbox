"""Clinical interpretation API routes."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from okbox.apps.variants.interpretation_models import (
    InterpretationHistory,
    InterpretationStatus,
    Pathogenicity,
    VariantInterpretation,
)
from okbox.apps.variants.interpretation_schemas import (
    InterpretationCreateRequest,
    InterpretationHistoryResponse,
    InterpretationResponse,
    InterpretationReviewRequest,
    InterpretationUpdateRequest,
)
from okbox.core.database import get_db
from okbox.core.exceptions import NotFoundException, ValidationException

router = APIRouter(prefix="/interpretations", tags=["interpretations"])


@router.post("", response_model=InterpretationResponse, status_code=201)
async def create_interpretation(
    request: InterpretationCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> InterpretationResponse:
    """Create a new clinical interpretation for a variant."""
    if not request.interpreted_by:
        raise ValidationException("interpreted_by is required for audit traceability")

    interpretation = VariantInterpretation(
        variant_id=request.variant_id,
        sample_id=request.sample_id,
        pathogenicity=request.pathogenicity,
        include_in_report=request.include_in_report,
        notes=request.notes,
        evidence=request.evidence,
        status=InterpretationStatus.INTERPRETED,
        interpreted_by=request.interpreted_by,
        interpreted_at=datetime.now(timezone.utc),
    )
    db.add(interpretation)
    await db.flush()

    # Record history
    history = InterpretationHistory(
        interpretation_id=interpretation.id,
        variant_id=request.variant_id,
        action="classify",
        new_pathogenicity=request.pathogenicity.value,
        new_status=InterpretationStatus.INTERPRETED.value,
        notes=request.notes,
        user_id=request.interpreted_by,
        username=None,
    )
    db.add(history)
    await db.flush()
    await db.refresh(interpretation)

    return InterpretationResponse.model_validate(interpretation)


@router.patch("/{interp_id}", response_model=InterpretationResponse)
async def update_interpretation(
    interp_id: uuid.UUID,
    request: InterpretationUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> InterpretationResponse:
    """Update a clinical interpretation."""
    result = await db.execute(
        select(VariantInterpretation).where(VariantInterpretation.id == interp_id)
    )
    interp = result.scalar_one_or_none()
    if not interp:
        raise NotFoundException("Interpretation not found")

    if interp.status == InterpretationStatus.REVIEWED:
        raise ValidationException("Cannot modify a reviewed interpretation")

    old_pathogenicity = interp.pathogenicity.value if interp.pathogenicity else None

    # Apply updates
    if request.pathogenicity is not None:
        interp.pathogenicity = request.pathogenicity
    if request.include_in_report is not None:
        interp.include_in_report = request.include_in_report
    if request.notes is not None:
        interp.notes = request.notes
    if request.evidence is not None:
        interp.evidence = request.evidence

    # Record history
    history = InterpretationHistory(
        interpretation_id=interp.id,
        variant_id=interp.variant_id,
        action="update",
        old_pathogenicity=old_pathogenicity,
        new_pathogenicity=interp.pathogenicity.value,
        notes=request.notes,
        user_id=interp.interpreted_by or uuid.uuid4(),  # Use original interpreter
    )
    db.add(history)
    await db.flush()
    await db.refresh(interp)

    return InterpretationResponse.model_validate(interp)


@router.post("/{interp_id}/review", response_model=InterpretationResponse)
async def review_interpretation(
    interp_id: uuid.UUID,
    request: InterpretationReviewRequest,
    db: AsyncSession = Depends(get_db),
) -> InterpretationResponse:
    """Review and approve an interpretation."""
    result = await db.execute(
        select(VariantInterpretation).where(VariantInterpretation.id == interp_id)
    )
    interp = result.scalar_one_or_none()
    if not interp:
        raise NotFoundException("Interpretation not found")

    if interp.status != InterpretationStatus.INTERPRETED:
        raise ValidationException("Only interpreted variants can be reviewed")

    old_status = interp.status.value
    interp.status = InterpretationStatus.REVIEWED
    interp.reviewed_by = request.reviewed_by
    interp.reviewed_at = datetime.now(timezone.utc)

    # Record history
    history = InterpretationHistory(
        interpretation_id=interp.id,
        variant_id=interp.variant_id,
        action="review",
        old_status=old_status,
        new_status=InterpretationStatus.REVIEWED.value,
        notes=request.notes,
        user_id=request.reviewed_by,
    )
    db.add(history)
    await db.flush()
    await db.refresh(interp)

    return InterpretationResponse.model_validate(interp)


@router.get("/variant/{variant_id}", response_model=list[InterpretationResponse])
async def get_variant_interpretations(
    variant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[InterpretationResponse]:
    """Get all interpretations for a variant."""
    result = await db.execute(
        select(VariantInterpretation)
        .where(VariantInterpretation.variant_id == variant_id)
        .order_by(VariantInterpretation.created_at.desc())
    )
    interps = result.scalars().all()
    return [InterpretationResponse.model_validate(i) for i in interps]


@router.get("/history/{interp_id}", response_model=list[InterpretationHistoryResponse])
async def get_interpretation_history(
    interp_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[InterpretationHistoryResponse]:
    """Get interpretation change history."""
    result = await db.execute(
        select(InterpretationHistory)
        .where(InterpretationHistory.interpretation_id == interp_id)
        .order_by(InterpretationHistory.created_at.desc())
    )
    history = result.scalars().all()
    return [InterpretationHistoryResponse.model_validate(h) for h in history]
