"""Variant data models."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from okbox.core.database import Base


class VariantType(str, enum.Enum):
    """Variant type classification."""

    SNV = "snv"
    INDEL = "indel"
    CNV = "cnv"
    FUSION = "fusion"
    SV = "sv"


class ClinicalSignificance(str, enum.Enum):
    """ACMG clinical significance classification."""

    PATHOGENIC = "pathogenic"
    LIKELY_PATHOGENIC = "likely_pathogenic"
    VUS = "vus"
    LIKELY_BENIGN = "likely_benign"
    BENIGN = "benign"


class Variant(Base):
    """Variant record parsed from VCF files."""

    __tablename__ = "variants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sample_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("samples.id"), nullable=False, index=True
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pipeline_tasks.id"), nullable=True
    )

    # Genomic position
    chromosome: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    ref_allele: Mapped[str] = mapped_column(String(500), nullable=False)
    alt_allele: Mapped[str] = mapped_column(String(500), nullable=False)

    # Variant classification
    variant_type: Mapped[VariantType] = mapped_column(Enum(VariantType), nullable=False)
    gene: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    transcript: Mapped[str | None] = mapped_column(String(50), nullable=True)
    hgvs_c: Mapped[str | None] = mapped_column(String(200), nullable=True)
    hgvs_p: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Quality metrics
    quality: Mapped[float | None] = mapped_column(Float, nullable=True)
    depth: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vaf: Mapped[float | None] = mapped_column(Float, nullable=True)  # Variant allele frequency
    filter_status: Mapped[str | None] = mapped_column(String(50), nullable=True)  # PASS, etc.

    # Annotation
    functional_impact: Mapped[str | None] = mapped_column(String(100), nullable=True)
    population_frequency: Mapped[float | None] = mapped_column(Float, nullable=True)
    clinical_significance: Mapped[ClinicalSignificance | None] = mapped_column(
        Enum(ClinicalSignificance), nullable=True
    )
    dbsnp_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cosmic_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    clinvar_id: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Full annotation as JSON (all INFO fields)
    annotations: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
