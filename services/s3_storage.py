"""
S3/MinIO storage service for document management.
"""
import os
import io
import hashlib
from typing import Optional, BinaryIO
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError

from utils.logger import app_logger


class S3StorageService:
    """S3-compatible storage service (works with AWS S3 and MinIO)."""

    def __init__(self):
        self.endpoint_url = os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")
        self.access_key = os.getenv("S3_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("S3_SECRET_KEY", "minioadmin")
        self.bucket_name = os.getenv("S3_BUCKET_NAME", "nanonets-documents")
        self.region = os.getenv("S3_REGION", "us-east-1")

        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region
        )

        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist."""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            try:
                self.client.create_bucket(Bucket=self.bucket_name)
                app_logger.info(f"Created bucket: {self.bucket_name}")
            except Exception as e:
                app_logger.warning(f"Could not create bucket: {e}")

    def upload_file(
        self,
        file_data: BinaryIO,
        filename: str,
        content_type: str = "application/octet-stream",
        tenant_id: str = "default",
        metadata: dict = None
    ) -> dict:
        """
        Upload a file to S3.

        Args:
            file_data: File-like object or bytes
            filename: Original filename
            content_type: MIME type
            tenant_id: Tenant identifier for path isolation
            metadata: Additional metadata

        Returns:
            Upload result with key and URL
        """
        # Generate unique key
        timestamp = datetime.utcnow().strftime("%Y/%m/%d")
        file_hash = hashlib.sha256(filename.encode()).hexdigest()[:8]
        key = f"{tenant_id}/{timestamp}/{file_hash}_{filename}"

        # Read file content
        if isinstance(file_data, bytes):
            content = file_data
        else:
            content = file_data.read()

        # Calculate file hash
        content_hash = hashlib.sha256(content).hexdigest()

        # Upload
        extra_args = {
            "ContentType": content_type,
            "Metadata": {
                "original_filename": filename,
                "content_hash": content_hash,
                "uploaded_at": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
        }

        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content,
                **extra_args
            )

            app_logger.info(
                "File uploaded to S3",
                key=key,
                size_bytes=len(content),
                tenant_id=tenant_id
            )

            return {
                "key": key,
                "bucket": self.bucket_name,
                "size_bytes": len(content),
                "content_hash": content_hash,
                "url": f"{self.endpoint_url}/{self.bucket_name}/{key}"
            }

        except Exception as e:
            app_logger.error(f"S3 upload failed: {e}")
            raise

    def download_file(self, key: str) -> bytes:
        """
        Download a file from S3.

        Args:
            key: S3 object key

        Returns:
            File content as bytes
        """
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            content = response['Body'].read()

            app_logger.info("File downloaded from S3", key=key)
            return content

        except Exception as e:
            app_logger.error(f"S3 download failed: {e}")
            raise

    def get_presigned_url(
        self,
        key: str,
        expires_in: int = 3600,
        method: str = "get_object"
    ) -> str:
        """
        Generate a presigned URL for temporary access.

        Args:
            key: S3 object key
            expires_in: URL expiration in seconds
            method: S3 operation (get_object, put_object)

        Returns:
            Presigned URL
        """
        try:
            url = self.client.generate_presigned_url(
                method,
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key
                },
                ExpiresIn=expires_in
            )
            return url

        except Exception as e:
            app_logger.error(f"Presigned URL generation failed: {e}")
            raise

    def delete_file(self, key: str) -> bool:
        """
        Delete a file from S3.

        Args:
            key: S3 object key

        Returns:
            True if deleted successfully
        """
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            app_logger.info("File deleted from S3", key=key)
            return True

        except Exception as e:
            app_logger.error(f"S3 delete failed: {e}")
            return False

    def list_files(
        self,
        prefix: str = "",
        max_keys: int = 1000
    ) -> list:
        """
        List files in S3 with optional prefix filter.

        Args:
            prefix: Key prefix filter
            max_keys: Maximum number of keys to return

        Returns:
            List of file metadata
        """
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )

            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat()
                })

            return files

        except Exception as e:
            app_logger.error(f"S3 list failed: {e}")
            return []

    def get_file_metadata(self, key: str) -> Optional[dict]:
        """
        Get metadata for a file.

        Args:
            key: S3 object key

        Returns:
            File metadata or None
        """
        try:
            response = self.client.head_object(
                Bucket=self.bucket_name,
                Key=key
            )

            return {
                'key': key,
                'size': response['ContentLength'],
                'content_type': response['ContentType'],
                'last_modified': response['LastModified'].isoformat(),
                'metadata': response.get('Metadata', {})
            }

        except ClientError:
            return None

    def health_check(self) -> bool:
        """Check if S3 is accessible."""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            return True
        except:
            return False


# Global instance
s3_storage = S3StorageService()
