"""Electronic signature API routes."""

import hashlib
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from okbox.apps.auth.models import User
from okbox.apps.auth.security import verify_password
from okbox.apps.reports.models import Report
from okbox.apps.signatures.models import Signature, SignatureRole, SignatureStatus
from okbox.apps.signatures.schemas import (
    SignRequest,
    SignatureResponse,
    VerifyResponse,
)
from okbox.core.database import get_db
from okbox.core.exceptions import ForbiddenException, NotFoundException, ValidationException

router = APIRouter(prefix="/signatures", tags=["signatures"])

# Signing order enforcement
SIGN_ORDER = [SignatureRole.ANALYST_REVIEW, SignatureRole.DOCTOR_REVIEW, SignatureRole.DIRECTOR_SIGN]


def _compute_report_hash(content: str) -> str:
    """Compute SHA256 hash of report content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


@router.post("/sign", response_model=SignatureResponse, status_code=201)
async def sign_report(
    request: SignRequest,
    db: AsyncSession = Depends(get_db),
) -> SignatureResponse:
    """Sign a report (requires password confirmation).

    Signing order: analyst_review -> doctor_review -> director_sign
    """
    # Verify report exists
    result = await db.execute(select(Report).where(Report.id == request.report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise NotFoundException("Report not found")

    if not report.html_content:
        raise ValidationException("Report has no content to sign")

    # Second-factor authentication: verify password
    user_result = await db.execute(select(User).where(User.id == request.signer_id))
    signer_user = user_result.scalar_one_or_none()
    if not signer_user:
        raise NotFoundException("Signer user not found")
    if not verify_password(request.password, signer_user.password_hash):
        raise ForbiddenException("Password verification failed - signature rejected")

    # Verify signing order
    existing_sigs = await db.execute(
        select(Signature)
        .where(Signature.report_id == request.report_id, Signature.status == SignatureStatus.SIGNED)
    )
    signed_roles = {sig.role for sig in existing_sigs.scalars().all()}

    # Check if previous roles are signed
    role_index = SIGN_ORDER.index(request.role)
    for i in range(role_index):
        if SIGN_ORDER[i] not in signed_roles:
            raise ValidationException(
                f"Cannot sign as {request.role.value}: {SIGN_ORDER[i].value} not yet signed"
            )

    # Check not already signed by this role
    if request.role in signed_roles:
        raise ValidationException(f"Report already signed as {request.role.value}")

    # Compute content hash
    content_hash = _compute_report_hash(report.html_content)

    signature = Signature(
        report_id=request.report_id,
        signer_id=request.signer_id,
        role=request.role,
        status=SignatureStatus.SIGNED,
        signer_name=request.signer_name,
        signer_qualification=request.signer_qualification,
        content_hash=content_hash,
        signature_timestamp=datetime.now(timezone.utc),
    )
    db.add(signature)
    await db.flush()
    await db.refresh(signature)

    return SignatureResponse.model_validate(signature)


@router.get("/report/{report_id}", response_model=list[SignatureResponse])
async def get_report_signatures(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[SignatureResponse]:
    """Get all signatures for a report."""
    result = await db.execute(
        select(Signature)
        .where(Signature.report_id == report_id)
        .order_by(Signature.created_at)
    )
    signatures = result.scalars().all()
    return [SignatureResponse.model_validate(s) for s in signatures]


@router.get("/verify/{report_id}", response_model=VerifyResponse)
async def verify_signatures(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> VerifyResponse:
    """Verify report signature integrity.

    Checks that report content hasn't been modified since signing.
    """
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise NotFoundException("Report not found")

    if not report.html_content:
        return VerifyResponse(valid=False, message="Report has no content")

    current_hash = _compute_report_hash(report.html_content)

    # Check all signatures
    sig_result = await db.execute(
        select(Signature)
        .where(Signature.report_id == report_id, Signature.status == SignatureStatus.SIGNED)
    )
    signatures = list(sig_result.scalars().all())

    if not signatures:
        return VerifyResponse(valid=False, message="No signatures found")

    # Verify each signature's hash matches current content
    for sig in signatures:
        if sig.content_hash != current_hash:
            return VerifyResponse(
                valid=False,
                message=f"Content modified after {sig.role.value} signature",
            )

    # Check if all required signatures are present
    signed_roles = {sig.role for sig in signatures}
    missing = [r.value for r in SIGN_ORDER if r not in signed_roles]

    if missing:
        return VerifyResponse(
            valid=True,
            message=f"Partially signed. Missing: {', '.join(missing)}",
        )

    return VerifyResponse(valid=True, message="All signatures valid and complete")
