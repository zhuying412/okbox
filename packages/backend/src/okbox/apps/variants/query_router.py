"""Variant query API routes for browsing and filtering."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from okbox.apps.variants.models import ClinicalSignificance, Variant, VariantType
from okbox.apps.variants.query_schemas import (
    VariantQueryParams,
    VariantResponse,
)
from okbox.core.database import get_db
from okbox.core.exceptions import NotFoundException

router = APIRouter(prefix="/variants", tags=["variants"])


@router.get("", response_model=dict)
async def query_variants(
    sample_id: uuid.UUID = Query(...),
    gene: str | None = Query(None),
    variant_type: VariantType | None = Query(None),
    chromosome: str | None = Query(None),
    min_vaf: float | None = Query(None),
    max_vaf: float | None = Query(None),
    min_depth: int | None = Query(None),
    max_population_frequency: float | None = Query(None),
    functional_impact: str | None = Query(None),
    clinical_significance: ClinicalSignificance | None = Query(None),
    filter_status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    sort_by: str = Query("position"),
    sort_order: str = Query("asc"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Query variants with multi-dimensional filtering.

    Supports filtering by gene, variant type, VAF, depth, population frequency,
    functional impact, clinical significance, etc.
    """
    stmt = select(Variant).where(Variant.sample_id == sample_id)
    count_stmt = select(sa_func.count(Variant.id)).where(Variant.sample_id == sample_id)

    # Apply filters
    if gene:
        stmt = stmt.where(Variant.gene.ilike(f"%{gene}%"))
        count_stmt = count_stmt.where(Variant.gene.ilike(f"%{gene}%"))
    if variant_type:
        stmt = stmt.where(Variant.variant_type == variant_type)
        count_stmt = count_stmt.where(Variant.variant_type == variant_type)
    if chromosome:
        stmt = stmt.where(Variant.chromosome == chromosome)
        count_stmt = count_stmt.where(Variant.chromosome == chromosome)
    if min_vaf is not None:
        stmt = stmt.where(Variant.vaf >= min_vaf)
        count_stmt = count_stmt.where(Variant.vaf >= min_vaf)
    if max_vaf is not None:
        stmt = stmt.where(Variant.vaf <= max_vaf)
        count_stmt = count_stmt.where(Variant.vaf <= max_vaf)
    if min_depth is not None:
        stmt = stmt.where(Variant.depth >= min_depth)
        count_stmt = count_stmt.where(Variant.depth >= min_depth)
    if max_population_frequency is not None:
        stmt = stmt.where(Variant.population_frequency <= max_population_frequency)
        count_stmt = count_stmt.where(Variant.population_frequency <= max_population_frequency)
    if functional_impact:
        stmt = stmt.where(Variant.functional_impact.ilike(f"%{functional_impact}%"))
        count_stmt = count_stmt.where(Variant.functional_impact.ilike(f"%{functional_impact}%"))
    if clinical_significance:
        stmt = stmt.where(Variant.clinical_significance == clinical_significance)
        count_stmt = count_stmt.where(Variant.clinical_significance == clinical_significance)
    if filter_status:
        stmt = stmt.where(Variant.filter_status == filter_status)
        count_stmt = count_stmt.where(Variant.filter_status == filter_status)

    # Sorting (whitelist to prevent probing internal attributes)
    ALLOWED_SORT_FIELDS = {
        "position", "chromosome", "gene", "vaf", "depth",
        "quality", "clinical_significance", "population_frequency",
        "variant_type", "filter_status",
    }
    if sort_by not in ALLOWED_SORT_FIELDS:
        sort_by = "position"
    sort_column = getattr(Variant, sort_by)
    if sort_order == "desc":
        stmt = stmt.order_by(sort_column.desc())
    else:
        stmt = stmt.order_by(sort_column.asc())

    # Get total
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Pagination
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    variants = list(result.scalars().all())

    return {
        "items": [VariantResponse.model_validate(v) for v in variants],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{variant_id}", response_model=VariantResponse)
async def get_variant_detail(
    variant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> VariantResponse:
    """Get full variant details with all annotations."""
    result = await db.execute(select(Variant).where(Variant.id == variant_id))
    variant = result.scalar_one_or_none()
    if not variant:
        raise NotFoundException("Variant not found")
    return VariantResponse.model_validate(variant)
