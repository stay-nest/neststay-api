"""Local filesystem storage implementation."""

from pathlib import Path


class LocalStorageService:
    """Store files on the local filesystem."""

    def __init__(self, upload_dir: str, base_url: str | None = None):
        """Initialize with upload dir and optional app URL for full HTTP URLs."""
        self.upload_dir = Path(upload_dir)
        self.base_url = base_url.rstrip("/") if base_url else None

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
        When base_url is set, returns a full HTTP URL (e.g. http://localhost:8000/uploads/...).

        Args:
            path: Relative path

        Returns:
            URL path e.g. /uploads/locations/1/uuid.jpg, or full URL when
            base_url is set
        """
        path_part = f"/uploads/{path}"
        if self.base_url:
            return f"{self.base_url}{path_part}"
        return path_part
