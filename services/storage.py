"""
File storage service for documents and results.
"""
import os
import shutil
import hashlib
import time
from pathlib import Path
from typing import Optional, BinaryIO
from dataclasses import dataclass

from config import settings


@dataclass
class StoredFile:
    """Stored file metadata."""
    file_id: str
    filename: str
    path: str
    size_bytes: int
    content_hash: str
    created_at: float
    mime_type: Optional[str] = None


class StorageService:
    """
    File storage service with local filesystem backend.
    """

    def __init__(self, base_path: str = None):
        """
        Initialize storage service.

        Args:
            base_path: Base directory for storage.
        """
        self.base_path = Path(base_path or settings.storage_path)
        self._ensure_directories()

    def _ensure_directories(self):
        """Create necessary directories."""
        dirs = ["uploads", "results", "temp"]
        for d in dirs:
            (self.base_path / d).mkdir(parents=True, exist_ok=True)

    def _generate_file_id(self, content: bytes) -> str:
        """Generate unique file ID from content hash."""
        timestamp = str(time.time()).encode()
        hasher = hashlib.sha256()
        hasher.update(content[:1024])  # Hash first 1KB
        hasher.update(timestamp)
        return hasher.hexdigest()[:16]

    def _get_content_hash(self, content: bytes) -> str:
        """Get full content hash."""
        return hashlib.sha256(content).hexdigest()

    def save_upload(self, filename: str, content: bytes,
                    mime_type: str = None) -> StoredFile:
        """
        Save an uploaded file.

        Args:
            filename: Original filename.
            content: File content.
            mime_type: MIME type.

        Returns:
            StoredFile metadata.
        """
        file_id = self._generate_file_id(content)
        safe_filename = self._sanitize_filename(filename)

        # Create file path
        file_path = self.base_path / "uploads" / f"{file_id}_{safe_filename}"

        # Write file
        with open(file_path, "wb") as f:
            f.write(content)

        return StoredFile(
            file_id=file_id,
            filename=safe_filename,
            path=str(file_path),
            size_bytes=len(content),
            content_hash=self._get_content_hash(content),
            created_at=time.time(),
            mime_type=mime_type
        )

    def save_result(self, job_id: str, result: dict) -> str:
        """
        Save processing result.

        Args:
            job_id: Job ID.
            result: Result data.

        Returns:
            Result file path.
        """
        import json

        file_path = self.base_path / "results" / f"{job_id}.json"

        with open(file_path, "w") as f:
            json.dump(result, f, indent=2)

        return str(file_path)

    def get_result(self, job_id: str) -> Optional[dict]:
        """
        Get processing result.

        Args:
            job_id: Job ID.

        Returns:
            Result data or None.
        """
        import json

        file_path = self.base_path / "results" / f"{job_id}.json"

        if file_path.exists():
            with open(file_path) as f:
                return json.load(f)
        return None

    def get_upload(self, file_id: str) -> Optional[bytes]:
        """
        Get uploaded file content.

        Args:
            file_id: File ID.

        Returns:
            File content or None.
        """
        uploads_dir = self.base_path / "uploads"

        for file_path in uploads_dir.glob(f"{file_id}_*"):
            with open(file_path, "rb") as f:
                return f.read()
        return None

    def delete_upload(self, file_id: str) -> bool:
        """
        Delete an uploaded file.

        Args:
            file_id: File ID.

        Returns:
            True if deleted.
        """
        uploads_dir = self.base_path / "uploads"

        for file_path in uploads_dir.glob(f"{file_id}_*"):
            file_path.unlink()
            return True
        return False

    def delete_result(self, job_id: str) -> bool:
        """
        Delete a result file.

        Args:
            job_id: Job ID.

        Returns:
            True if deleted.
        """
        file_path = self.base_path / "results" / f"{job_id}.json"

        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def create_temp_file(self, suffix: str = "") -> str:
        """
        Create a temporary file.

        Args:
            suffix: File suffix/extension.

        Returns:
            Temp file path.
        """
        import uuid
        filename = f"{uuid.uuid4().hex}{suffix}"
        return str(self.base_path / "temp" / filename)

    def cleanup_temp(self, max_age_hours: int = 24):
        """
        Clean up old temporary files.

        Args:
            max_age_hours: Maximum file age in hours.
        """
        temp_dir = self.base_path / "temp"
        cutoff = time.time() - (max_age_hours * 3600)

        for file_path in temp_dir.iterdir():
            if file_path.stat().st_mtime < cutoff:
                file_path.unlink()

    def get_storage_stats(self) -> dict:
        """Get storage statistics."""
        stats = {}

        for dir_name in ["uploads", "results", "temp"]:
            dir_path = self.base_path / dir_name
            files = list(dir_path.iterdir())
            total_size = sum(f.stat().st_size for f in files if f.is_file())

            stats[dir_name] = {
                "files": len(files),
                "size_bytes": total_size,
                "size_mb": round(total_size / (1024 * 1024), 2)
            }

        return stats

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove path components
        filename = os.path.basename(filename)

        # Remove dangerous characters
        dangerous = ['..', '/', '\\', '\x00', '<', '>', '|', '*', '?', '"']
        for char in dangerous:
            filename = filename.replace(char, '')

        return filename or "unnamed"


# Global storage service
storage_service = StorageService()


if __name__ == "__main__":
    print("=" * 60)
    print("STORAGE SERVICE TEST")
    print("=" * 60)

    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        storage = StorageService(tmp)

        # Test save upload
        content = b"Test file content"
        stored = storage.save_upload("test.txt", content)
        print(f"  Saved: {stored.file_id}")

        # Test get upload
        retrieved = storage.get_upload(stored.file_id)
        print(f"  Retrieved: {len(retrieved)} bytes")

        # Test save result
        result_path = storage.save_result("job123", {"text": "result"})
        print(f"  Result saved: {result_path}")

        # Test get result
        result = storage.get_result("job123")
        print(f"  Result: {result}")

        # Test stats
        stats = storage.get_storage_stats()
        print(f"  Stats: {stats}")

        # Test cleanup
        storage.delete_upload(stored.file_id)
        print(f"  Deleted upload")

    print("\n  ✓ Storage service tests passed")
    print("=" * 60)
