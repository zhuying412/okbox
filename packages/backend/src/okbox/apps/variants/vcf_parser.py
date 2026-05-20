"""VCF 4.x file parser.

Parses standard VCF format files and extracts variant records
with annotation information from INFO fields.
"""

import logging
import re
import uuid
from dataclasses import dataclass, field
from typing import TextIO

from okbox.apps.variants.models import VariantType

logger = logging.getLogger(__name__)


@dataclass
class ParsedVariant:
    """A single parsed variant from VCF."""

    chromosome: str
    position: int
    ref_allele: str
    alt_allele: str
    quality: float | None = None
    filter_status: str | None = None
    variant_type: VariantType = VariantType.SNV
    gene: str | None = None
    transcript: str | None = None
    hgvs_c: str | None = None
    hgvs_p: str | None = None
    depth: int | None = None
    vaf: float | None = None
    functional_impact: str | None = None
    population_frequency: float | None = None
    dbsnp_id: str | None = None
    cosmic_id: str | None = None
    clinvar_id: str | None = None
    annotations: dict = field(default_factory=dict)


def determine_variant_type(ref: str, alt: str) -> VariantType:
    """Determine variant type from REF and ALT alleles."""
    if len(ref) == 1 and len(alt) == 1:
        return VariantType.SNV
    elif alt.startswith("<DEL>") or alt.startswith("<DUP>") or alt.startswith("<CNV>"):
        return VariantType.CNV
    elif ":" in alt or "]" in alt or "[" in alt:
        return VariantType.FUSION
    elif len(ref) != len(alt):
        return VariantType.INDEL
    else:
        return VariantType.SNV


def parse_info_field(info_str: str) -> dict:
    """Parse VCF INFO field into a dictionary."""
    info = {}
    if info_str == "." or not info_str:
        return info

    for item in info_str.split(";"):
        if "=" in item:
            key, value = item.split("=", 1)
            info[key] = value
        else:
            info[item] = True
    return info


def extract_annotation(info: dict) -> dict:
    """Extract annotation fields from INFO dictionary.

    Supports common annotation tools: VEP (CSQ), SnpEff (ANN), ANNOVAR.
    """
    result: dict = {}

    # VEP annotation (CSQ field)
    if "CSQ" in info:
        result["vep_csq"] = info["CSQ"]

    # SnpEff annotation (ANN field)
    if "ANN" in info:
        result["snpeff_ann"] = info["ANN"]

    # Common annotation fields
    for key in ("GENE", "Gene.refGene", "SYMBOL"):
        if key in info:
            result["gene"] = info[key]
            break

    for key in ("HGVSc", "AAChange.refGene"):
        if key in info:
            result["hgvs_c"] = info[key]
            break

    for key in ("HGVSp",):
        if key in info:
            result["hgvs_p"] = info[key]

    for key in ("AF", "gnomAD_AF", "ExAC_AF", "1000g2015aug_all"):
        if key in info:
            try:
                result["population_frequency"] = float(info[key])
            except (ValueError, TypeError):
                pass
            break

    for key in ("CLNSIG", "ClinVar_SIG"):
        if key in info:
            result["clinical_significance"] = info[key]
            break

    for key in ("Func.refGene", "Consequence", "ExonicFunc.refGene"):
        if key in info:
            result["functional_impact"] = info[key]
            break

    if "DB" in info or "RS" in info:
        result["dbsnp_id"] = info.get("RS", "")

    if "COSMIC_ID" in info:
        result["cosmic_id"] = info["COSMIC_ID"]

    return result


def parse_vcf(
    file_content: TextIO,
    sample_id: uuid.UUID,
    task_id: uuid.UUID | None = None,
) -> list[ParsedVariant]:
    """Parse a VCF file and return structured variant records.

    Supports VCF 4.x format with common annotation tools.
    """
    variants: list[ParsedVariant] = []
    line_num = 0

    for line in file_content:
        line_num += 1
        line = line.strip()

        # Skip headers
        if line.startswith("#") or not line:
            continue

        try:
            fields = line.split("\t")
            if len(fields) < 8:
                logger.warning("Line %d: insufficient fields (%d)", line_num, len(fields))
                continue

            chrom = fields[0]
            pos = int(fields[1])
            # id_field = fields[2]  # RS ID
            ref = fields[3]
            alt_field = fields[4]
            qual = float(fields[5]) if fields[5] != "." else None
            filter_status = fields[6]
            info_str = fields[7]

            # Parse INFO
            info = parse_info_field(info_str)
            annotation = extract_annotation(info)

            # Handle multi-allelic sites
            alt_alleles = alt_field.split(",")

            # Extract depth and VAF from FORMAT/sample columns if available
            depth = None
            vaf = None
            if "DP" in info:
                try:
                    depth = int(info["DP"])
                except (ValueError, TypeError):
                    pass
            if "AF" in info:
                try:
                    vaf = float(info["AF"].split(",")[0])
                except (ValueError, TypeError):
                    pass

            # Parse sample FORMAT fields for DP/AD/AF
            if len(fields) >= 10:
                format_field = fields[8]
                sample_field = fields[9]
                format_keys = format_field.split(":")
                sample_values = sample_field.split(":")
                sample_data = dict(zip(format_keys, sample_values))

                if "DP" in sample_data and depth is None:
                    try:
                        depth = int(sample_data["DP"])
                    except (ValueError, TypeError):
                        pass
                if "AF" in sample_data and vaf is None:
                    try:
                        vaf = float(sample_data["AF"].split(",")[0])
                    except (ValueError, TypeError):
                        pass
                elif "AD" in sample_data and vaf is None and depth:
                    try:
                        ad_values = [int(x) for x in sample_data["AD"].split(",")]
                        if len(ad_values) >= 2 and sum(ad_values) > 0:
                            vaf = ad_values[1] / sum(ad_values)
                    except (ValueError, TypeError):
                        pass

            for alt in alt_alleles:
                variant = ParsedVariant(
                    chromosome=chrom,
                    position=pos,
                    ref_allele=ref,
                    alt_allele=alt,
                    quality=qual,
                    filter_status=filter_status,
                    variant_type=determine_variant_type(ref, alt),
                    gene=annotation.get("gene"),
                    hgvs_c=annotation.get("hgvs_c"),
                    hgvs_p=annotation.get("hgvs_p"),
                    depth=depth,
                    vaf=vaf,
                    functional_impact=annotation.get("functional_impact"),
                    population_frequency=annotation.get("population_frequency"),
                    dbsnp_id=annotation.get("dbsnp_id"),
                    cosmic_id=annotation.get("cosmic_id"),
                    annotations=info,
                )
                variants.append(variant)

        except Exception as e:
            logger.error("Line %d: parse error: %s", line_num, str(e))
            continue

    logger.info("Parsed %d variants from VCF", len(variants))
    return variants
