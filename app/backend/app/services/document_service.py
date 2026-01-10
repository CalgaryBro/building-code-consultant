"""
Document upload and management service for permit applications.

This service handles:
- File upload validation (type, size)
- Secure file storage with unique paths
- File retrieval and deletion
- Document metadata management
"""
import os
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, BinaryIO
from fastapi import UploadFile, HTTPException

from ..config import get_settings

settings = get_settings()


# Allowed file types for upload
ALLOWED_FILE_TYPES = {
    # PDF documents
    "application/pdf": ".pdf",
    # Images
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/gif": ".gif",
    "image/tiff": ".tiff",
    "image/bmp": ".bmp",
    # CAD files
    "application/acad": ".dwg",
    "image/vnd.dwg": ".dwg",
    "application/x-autocad": ".dwg",
    "application/x-dwg": ".dwg",
    "application/dxf": ".dxf",
    # Microsoft Office
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
}

# Maximum file size in bytes (50 MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

# Document type categories
DOCUMENT_TYPES = {
    "site_plan": "Site plan showing property boundaries, setbacks, and structures",
    "floor_plan": "Floor plans for each level of the building",
    "elevation": "Building elevations (front, rear, sides)",
    "section": "Building cross-sections",
    "structural": "Structural drawings and calculations",
    "mechanical": "Mechanical/HVAC drawings",
    "electrical": "Electrical drawings",
    "plumbing": "Plumbing drawings",
    "energy_compliance": "Energy compliance documentation (NECB/9.36)",
    "survey": "Survey or real property report",
    "title": "Certificate of title",
    "geotechnical": "Geotechnical report",
    "drainage": "Drainage and grading plan",
    "landscape": "Landscape plan",
    "parking": "Parking layout",
    "signage": "Signage drawings",
    "fire_safety": "Fire safety plan",
    "accessibility": "Accessibility compliance documentation",
    "other": "Other supporting documents",
}


class DocumentService:
    """
    Service for handling document uploads and storage.
    """

    def __init__(self, upload_dir: Optional[str] = None):
        """
        Initialize the document service.

        Args:
            upload_dir: Base directory for file uploads.
                       Defaults to data/uploads in the project root.
        """
        if upload_dir:
            self.upload_dir = Path(upload_dir)
        else:
            self.upload_dir = Path(settings.data_dir) / "uploads"

        # Ensure upload directory exists
        self._ensure_upload_dir()

    def _ensure_upload_dir(self):
        """Create the upload directory structure if it doesn't exist."""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        (self.upload_dir / "permits").mkdir(exist_ok=True)
        (self.upload_dir / "temp").mkdir(exist_ok=True)

    def validate_file(
        self,
        file: UploadFile,
        max_size: int = MAX_FILE_SIZE,
        allowed_types: Optional[dict] = None
    ) -> Tuple[bool, str]:
        """
        Validate an uploaded file.

        Args:
            file: The uploaded file to validate.
            max_size: Maximum allowed file size in bytes.
            allowed_types: Dictionary of allowed MIME types and extensions.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if allowed_types is None:
            allowed_types = ALLOWED_FILE_TYPES

        # Check if file exists
        if not file:
            return False, "No file provided"

        # Check filename
        if not file.filename:
            return False, "File has no filename"

        # Check content type
        content_type = file.content_type or ""
        if content_type not in allowed_types:
            # Try to determine type from extension
            ext = Path(file.filename).suffix.lower()
            valid_extensions = list(allowed_types.values())
            if ext not in valid_extensions:
                return False, f"File type '{content_type}' is not allowed. Allowed types: PDF, images (PNG, JPEG, GIF, TIFF), CAD files (DWG, DXF)"

        # Check file size (we'll do this during save since we need to read the file)
        # For now, just return valid
        return True, ""

    def generate_file_path(
        self,
        permit_application_id: str,
        filename: str,
        document_id: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Generate a secure file path for storage.

        Args:
            permit_application_id: ID of the permit application.
            filename: Original filename.
            document_id: Optional document ID. Generated if not provided.

        Returns:
            Tuple of (relative_path, absolute_path).
        """
        if not document_id:
            document_id = str(uuid.uuid4())

        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)

        # Create path: uploads/permits/{application_id}/{document_id}_{filename}
        relative_path = f"permits/{permit_application_id}/{document_id}_{safe_filename}"
        absolute_path = self.upload_dir / relative_path

        return relative_path, str(absolute_path)

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename to prevent path traversal and other issues.

        Args:
            filename: Original filename.

        Returns:
            Sanitized filename.
        """
        # Get just the filename, not the path
        filename = Path(filename).name

        # Replace potentially dangerous characters
        dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*', '\0']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')

        # Limit length
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200-len(ext)] + ext

        return filename

    async def save_file(
        self,
        file: UploadFile,
        permit_application_id: str,
        document_id: Optional[str] = None,
        validate: bool = True
    ) -> Tuple[str, str, int]:
        """
        Save an uploaded file to storage.

        Args:
            file: The uploaded file.
            permit_application_id: ID of the permit application.
            document_id: Optional document ID.
            validate: Whether to validate the file before saving.

        Returns:
            Tuple of (relative_path, absolute_path, file_size_bytes).

        Raises:
            HTTPException: If validation fails or file cannot be saved.
        """
        # Validate file
        if validate:
            is_valid, error = self.validate_file(file)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error)

        # Generate paths
        relative_path, absolute_path = self.generate_file_path(
            permit_application_id,
            file.filename,
            document_id
        )

        # Ensure directory exists
        Path(absolute_path).parent.mkdir(parents=True, exist_ok=True)

        # Save file and track size
        file_size = 0
        try:
            with open(absolute_path, "wb") as buffer:
                while chunk := await file.read(8192):  # Read in 8KB chunks
                    file_size += len(chunk)
                    if file_size > MAX_FILE_SIZE:
                        # Clean up partial file
                        os.unlink(absolute_path)
                        raise HTTPException(
                            status_code=400,
                            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024):.1f} MB"
                        )
                    buffer.write(chunk)
        except HTTPException:
            raise
        except Exception as e:
            if os.path.exists(absolute_path):
                os.unlink(absolute_path)
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

        return relative_path, absolute_path, file_size

    def save_file_sync(
        self,
        file_content: bytes,
        permit_application_id: str,
        filename: str,
        document_id: Optional[str] = None
    ) -> Tuple[str, str, int]:
        """
        Synchronously save file content to storage.

        Args:
            file_content: The file content as bytes.
            permit_application_id: ID of the permit application.
            filename: Original filename.
            document_id: Optional document ID.

        Returns:
            Tuple of (relative_path, absolute_path, file_size_bytes).
        """
        # Check size
        file_size = len(file_content)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024):.1f} MB"
            )

        # Generate paths
        relative_path, absolute_path = self.generate_file_path(
            permit_application_id,
            filename,
            document_id
        )

        # Ensure directory exists
        Path(absolute_path).parent.mkdir(parents=True, exist_ok=True)

        # Save file
        try:
            with open(absolute_path, "wb") as buffer:
                buffer.write(file_content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

        return relative_path, absolute_path, file_size

    def get_file_path(self, relative_path: str) -> Optional[str]:
        """
        Get the absolute path for a stored file.

        Args:
            relative_path: The relative path stored in the database.

        Returns:
            Absolute file path if file exists, None otherwise.
        """
        absolute_path = self.upload_dir / relative_path
        if absolute_path.exists():
            return str(absolute_path)
        return None

    def delete_file(self, relative_path: str) -> bool:
        """
        Delete a stored file.

        Args:
            relative_path: The relative path of the file to delete.

        Returns:
            True if file was deleted, False if file didn't exist.
        """
        absolute_path = self.upload_dir / relative_path
        if absolute_path.exists():
            try:
                os.unlink(absolute_path)
                # Try to remove empty parent directories
                self._cleanup_empty_dirs(absolute_path.parent)
                return True
            except Exception:
                return False
        return False

    def _cleanup_empty_dirs(self, directory: Path):
        """
        Remove empty directories up to the upload base directory.

        Args:
            directory: Starting directory to check.
        """
        try:
            while directory != self.upload_dir and directory.exists():
                if not any(directory.iterdir()):
                    directory.rmdir()
                    directory = directory.parent
                else:
                    break
        except Exception:
            pass  # Ignore cleanup errors

    def delete_permit_files(self, permit_application_id: str) -> int:
        """
        Delete all files associated with a permit application.

        Args:
            permit_application_id: ID of the permit application.

        Returns:
            Number of files deleted.
        """
        permit_dir = self.upload_dir / "permits" / permit_application_id
        deleted_count = 0

        if permit_dir.exists():
            for file_path in permit_dir.glob("*"):
                if file_path.is_file():
                    try:
                        os.unlink(file_path)
                        deleted_count += 1
                    except Exception:
                        pass

            # Remove the permit directory
            try:
                shutil.rmtree(permit_dir)
            except Exception:
                pass

        return deleted_count

    def get_document_types(self) -> dict:
        """
        Get the list of valid document types and their descriptions.

        Returns:
            Dictionary of document type codes and descriptions.
        """
        return DOCUMENT_TYPES.copy()

    def get_allowed_file_types(self) -> List[str]:
        """
        Get the list of allowed file extensions.

        Returns:
            List of allowed file extensions.
        """
        return list(set(ALLOWED_FILE_TYPES.values()))

    def get_max_file_size(self) -> int:
        """
        Get the maximum allowed file size in bytes.

        Returns:
            Maximum file size in bytes.
        """
        return MAX_FILE_SIZE

    def get_storage_stats(self, permit_application_id: Optional[str] = None) -> dict:
        """
        Get storage statistics.

        Args:
            permit_application_id: Optional permit application ID to filter by.

        Returns:
            Dictionary with storage statistics.
        """
        if permit_application_id:
            target_dir = self.upload_dir / "permits" / permit_application_id
        else:
            target_dir = self.upload_dir / "permits"

        if not target_dir.exists():
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0.0
            }

        total_files = 0
        total_size = 0

        for file_path in target_dir.rglob("*"):
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size

        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }


# Create a singleton instance
document_service = DocumentService()
