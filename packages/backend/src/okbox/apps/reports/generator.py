"""Report generation engine.

Generates HTML reports from templates with variable interpolation,
then converts to PDF using WeasyPrint.
"""

import logging
import os
import uuid
from datetime import datetime
from string import Template

logger = logging.getLogger(__name__)

REPORTS_OUTPUT_DIR = os.environ.get("REPORTS_DIR", "/data/reports")


def render_html_report(template_html: str, context: dict) -> str:
    """Render an HTML report from a template with context variables.

    Template uses ${variable} syntax for interpolation.
    Context should include: patient_info, sample_info, qc_results,
    variant_list, interpretation_summary, conclusion.
    """
    try:
        tmpl = Template(template_html)
        return tmpl.safe_substitute(context)
    except Exception as e:
        logger.error("Template rendering failed: %s", str(e))
        raise ValueError(f"Report rendering failed: {str(e)}")


def generate_pdf_from_html(html_content: str, report_id: str) -> str:
    """Convert HTML content to PDF using WeasyPrint.

    Returns the path to the generated PDF file.
    """
    os.makedirs(REPORTS_OUTPUT_DIR, exist_ok=True)
    pdf_path = os.path.join(REPORTS_OUTPUT_DIR, f"{report_id}.pdf")

    try:
        # WeasyPrint import - optional dependency
        from weasyprint import HTML

        html_doc = HTML(string=html_content)
        html_doc.write_pdf(pdf_path)
        logger.info("Generated PDF: %s", pdf_path)
        return pdf_path
    except ImportError:
        logger.warning("WeasyPrint not installed, skipping PDF generation")
        # Fallback: save HTML as file
        html_path = os.path.join(REPORTS_OUTPUT_DIR, f"{report_id}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return html_path
    except Exception as e:
        logger.error("PDF generation failed: %s", str(e))
        raise RuntimeError(f"PDF generation failed: {str(e)}")


def build_report_context(
    patient_info: dict,
    sample_info: dict,
    qc_results: dict | None,
    variants: list[dict],
    interpretations: list[dict],
) -> dict:
    """Build the template context from various data sources."""
    # Format variant table rows
    variant_rows = ""
    for v in variants:
        variant_rows += f"""<tr>
            <td>{v.get('gene', '-')}</td>
            <td>{v.get('chromosome', '')}:{v.get('position', '')}</td>
            <td>{v.get('hgvs_c', '-')}</td>
            <td>{v.get('hgvs_p', '-')}</td>
            <td>{v.get('vaf', '-')}</td>
            <td>{v.get('pathogenicity', '-')}</td>
        </tr>"""

    return {
        "report_date": datetime.now().strftime("%Y-%m-%d"),
        "patient_name": patient_info.get("name", "-"),
        "patient_no": patient_info.get("patient_no", "-"),
        "patient_gender": patient_info.get("gender", "-"),
        "patient_age": patient_info.get("age", "-"),
        "sample_no": sample_info.get("sample_no", "-"),
        "sample_type": sample_info.get("sample_type", "-"),
        "panel_type": sample_info.get("panel_type", "-"),
        "received_date": sample_info.get("received_date", "-"),
        "qc_mean_depth": str(qc_results.get("mean_depth", "-")) if qc_results else "-",
        "qc_coverage": str(qc_results.get("coverage_30x", "-")) if qc_results else "-",
        "variant_count": str(len(variants)),
        "variant_table_rows": variant_rows,
        "conclusion": "See detailed variant interpretation below.",
    }
