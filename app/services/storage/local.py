"""Local filesystem storage implementation."""

from pathlib import Path


class LocalStorageService:
    """Store files on the local filesystem."""

    def __init__(self, upload_dir: str):
        """Initialize with the base upload directory."""
        self.upload_dir = Path(upload_dir)

    def save(self, file_content: bytes, filename: str, path: str) -> str:
        """
        Save file to {upload_dir}/{path}. Create parent dirs as needed.

        Args:
            file_content: Raw file bytes
            filename: Original filename (unused; path already includes name)
            path: Relative path e.g. locations/1/uuid.jpg

        Returns:
            Relative path as stored (e.g. locations/1/uuid.jpg)
        """
        full_path = self.upload_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(file_content)
        return path

    def delete(self, path: str) -> None:
        """
        Delete file at {upload_dir}/{path} if it exists.

        Args:
            path: Relative path to the file
        """
        full_path = self.upload_dir / path
        if full_path.exists():
            full_path.unlink()

    def get_url(self, path: str) -> str:
        """
        Return the public URL for a stored file (served under /uploads).

        Args:
            path: Relative path

        Returns:
            URL path e.g. /uploads/locations/1/uuid.jpg
        """
        return f"/uploads/{path}"
