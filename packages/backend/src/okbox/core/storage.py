"""MinIO object storage client.

Handles file upload, download, and management for FASTQ and other large files.
Storage path convention: {bucket}/{sample_id}/{filename}
"""

import hashlib
import io
import logging
from typing import BinaryIO

from miniio import Minio  # type: ignore[import-untyped]

from okbox.core.config import settings

logger = logging.getLogger(__name__)


def get_minio_client() -> Minio:
    """Create a MinIO client instance."""
    return Minio(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_use_ssl,
    )


def ensure_bucket(client: Minio, bucket: str | None = None) -> None:
    """Ensure the storage bucket exists."""
    bucket_name = bucket or settings.minio_bucket
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        logger.info("Created bucket: %s", bucket_name)


def build_object_path(sample_id: str, filename: str) -> str:
    """Build a standardized object storage path.

    Convention: samples/{sample_id}/{filename}
    """
    return f"samples/{sample_id}/{filename}"


def compute_file_hash(data: bytes, algorithm: str = "sha256") -> str:
    """Compute hash of file content for integrity verification."""
    h = hashlib.new(algorithm)
    h.update(data)
    return h.hexdigest()


class StorageService:
    """High-level storage operations for file management."""

    def __init__(self):
        self.client = get_minio_client()
        self.bucket = settings.minio_bucket

    def init(self) -> None:
        """Initialize storage (ensure bucket exists)."""
        ensure_bucket(self.client, self.bucket)

    def upload_file(
        self,
        object_path: str,
        data: BinaryIO,
        length: int,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload a file to object storage.

        Returns the object path (etag).
        """
        result = self.client.put_object(
            self.bucket,
            object_path,
            data,
            length=length,
            content_type=content_type,
        )
        return result.etag

    def upload_chunk(
        self,
        upload_id: str,
        object_path: str,
        part_number: int,
        data: bytes,
    ) -> str:
        """Upload a single chunk as part of multipart upload.

        Returns the ETag for this part.
        """
        stream = io.BytesIO(data)
        result = self.client.put_object(
            self.bucket,
            f"{object_path}.part{part_number:05d}",
            stream,
            length=len(data),
        )
        return result.etag

    def get_presigned_url(self, object_path: str, expires_hours: int = 1) -> str:
        """Generate a presigned URL for download."""
        from datetime import timedelta

        return self.client.presigned_get_object(
            self.bucket,
            object_path,
            expires=timedelta(hours=expires_hours),
        )

    def delete_file(self, object_path: str) -> None:
        """Delete a file from storage."""
        self.client.remove_object(self.bucket, object_path)

    def file_exists(self, object_path: str) -> bool:
        """Check if a file exists in storage."""
        try:
            self.client.stat_object(self.bucket, object_path)
            return True
        except Exception:
            return False
