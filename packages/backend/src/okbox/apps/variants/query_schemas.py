"""Variant query and response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from okbox.apps.variants.models import ClinicalSignificance, VariantType


class VariantResponse(BaseModel):
    """Variant response for listing."""

    id: uuid.UUID
    sample_id: uuid.UUID
    chromosome: str
    position: int
    ref_allele: str
    alt_allele: str
    variant_type: VariantType
    gene: str | None
    transcript: str | None
    hgvs_c: str | None
    hgvs_p: str | None
    quality: float | None
    depth: int | None
    vaf: float | None
    filter_status: str | None
    functional_impact: str | None
    population_frequency: float | None
    clinical_significance: ClinicalSignificance | None
    dbsnp_id: str | None
    cosmic_id: str | None
    clinvar_id: str | None
    annotations: dict | None
    created_at: datetime

    class Config:
        from_attributes = True


class VariantQueryParams(BaseModel):
    """Query parameters for variant filtering."""

    sample_id: uuid.UUID
    gene: str | None = None
    variant_type: VariantType | None = None
    chromosome: str | None = None
    min_vaf: float | None = None
    max_vaf: float | None = None
    min_depth: int | None = None
    max_population_frequency: float | None = None
    functional_impact: str | None = None
    clinical_significance: ClinicalSignificance | None = None
    filter_status: str | None = None
    page: int = 1
    page_size: int = 50
    sort_by: str = "position"
    sort_order: str = "asc"


class FilterTemplateCreate(BaseModel):
    """Create a saved filter template."""

    name: str = Field(..., min_length=1, max_length=100)
    filters: dict


class FilterTemplateResponse(BaseModel):
    """Saved filter template response."""

    id: uuid.UUID
    name: str
    filters: dict
    created_at: datetime

    class Config:
        from_attributes = True
