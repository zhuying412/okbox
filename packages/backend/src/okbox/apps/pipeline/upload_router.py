"""FASTQ file upload API routes.

Supports chunked upload with resume capability for large FASTQ files (50GB+).
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from okbox.apps.pipeline.models import FileRecord, UploadStatus
from okbox.apps.pipeline.schemas import (
    ChunkUploadResponse,
    FileRecordResponse,
    UploadCompleteRequest,
    UploadInitRequest,
    UploadInitResponse,
    UploadProgressResponse,
)
from okbox.core.database import get_db
from okbox.core.exceptions import NotFoundException, ValidationException
from okbox.core.storage import StorageService, build_object_path

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload/init", response_model=UploadInitResponse, status_code=201)
async def init_upload(
    request: UploadInitRequest,
    db: AsyncSession = Depends(get_db),
) -> UploadInitResponse:
    """Initiate a chunked file upload.

    Returns an upload_id to use for subsequent chunk uploads.
    """
    object_path = build_object_path(str(request.sample_id), request.filename)

    file_record = FileRecord(
        filename=request.filename,
        object_path=object_path,
        content_type=request.content_type,
        file_size=request.file_size,
        checksum_sha256=request.checksum_sha256,
        sample_id=request.sample_id,
        total_chunks=request.total_chunks,
        upload_status=UploadStatus.UPLOADING,
    )
    db.add(file_record)
    await db.flush()
    await db.refresh(file_record)

    return UploadInitResponse(
        upload_id=file_record.id,
        object_path=object_path,
        total_chunks=request.total_chunks,
    )


@router.post("/upload/{upload_id}/chunk/{chunk_number}", response_model=ChunkUploadResponse)
async def upload_chunk(
    upload_id: uuid.UUID,
    chunk_number: int,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
) -> ChunkUploadResponse:
    """Upload a single chunk of a file.

    Supports resume: if a chunk was already uploaded, it will be overwritten.
    """
    result = await db.execute(select(FileRecord).where(FileRecord.id == upload_id))
    record = result.scalar_one_or_none()
    if not record:
        raise NotFoundException("Upload not found")

    if record.upload_status == UploadStatus.COMPLETED:
        raise ValidationException("Upload already completed")

    if chunk_number < 1 or chunk_number > record.total_chunks:
        raise ValidationException(f"Invalid chunk number: {chunk_number}")

    # Read chunk data
    chunk_data = await file.read()

    # Store chunk via MinIO
    storage = StorageService()
    storage.upload_chunk(
        upload_id=str(upload_id),
        object_path=record.object_path,
        part_number=chunk_number,
        data=chunk_data,
    )

    # Update progress
    record.uploaded_chunks = chunk_number
    await db.flush()

    completed = record.uploaded_chunks >= record.total_chunks

    return ChunkUploadResponse(
        upload_id=upload_id,
        chunk_number=chunk_number,
        uploaded_chunks=record.uploaded_chunks,
        total_chunks=record.total_chunks,
        completed=completed,
    )


@router.post("/upload/{upload_id}/complete", response_model=FileRecordResponse)
async def complete_upload(
    upload_id: uuid.UUID,
    request: UploadCompleteRequest,
    db: AsyncSession = Depends(get_db),
) -> FileRecordResponse:
    """Mark an upload as complete after all chunks are uploaded."""
    result = await db.execute(select(FileRecord).where(FileRecord.id == upload_id))
    record = result.scalar_one_or_none()
    if not record:
        raise NotFoundException("Upload not found")

    if record.uploaded_chunks < record.total_chunks:
        raise ValidationException(
            f"Not all chunks uploaded: {record.uploaded_chunks}/{record.total_chunks}"
        )

    # Update checksum if provided
    if request.checksum_sha256:
        record.checksum_sha256 = request.checksum_sha256

    record.upload_status = UploadStatus.COMPLETED
    record.completed_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(record)

    return FileRecordResponse.model_validate(record)


@router.get("/upload/{upload_id}/progress", response_model=UploadProgressResponse)
async def get_upload_progress(
    upload_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> UploadProgressResponse:
    """Get upload progress for resume support."""
    result = await db.execute(select(FileRecord).where(FileRecord.id == upload_id))
    record = result.scalar_one_or_none()
    if not record:
        raise NotFoundException("Upload not found")

    progress = (record.uploaded_chunks / record.total_chunks * 100) if record.total_chunks > 0 else 0

    return UploadProgressResponse(
        upload_id=record.id,
        filename=record.filename,
        file_size=record.file_size,
        uploaded_chunks=record.uploaded_chunks,
        total_chunks=record.total_chunks,
        status=record.upload_status,
        progress_percent=round(progress, 2),
    )


@router.get("/sample/{sample_id}", response_model=list[FileRecordResponse])
async def list_sample_files(
    sample_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[FileRecordResponse]:
    """List all files associated with a sample."""
    result = await db.execute(
        select(FileRecord)
        .where(FileRecord.sample_id == sample_id)
        .order_by(FileRecord.created_at.desc())
    )
    records = result.scalars().all()
    return [FileRecordResponse.model_validate(r) for r in records]
