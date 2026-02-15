"""Unit tests for location image schemas (LocationImageRead vs LocationImageReadEmbedded)."""

from datetime import datetime

from app.schemas.location_image_schema import (
    LocationImageRead,
    LocationImageReadEmbedded,
)


class TestLocationImageRead:
    """Full image response schema includes id and location_id."""

    def test_has_id_and_location_id_fields(self) -> None:
        assert "id" in LocationImageRead.model_fields
        assert "location_id" in LocationImageRead.model_fields

    def test_roundtrip_with_id_and_location_id(self) -> None:
        data = {
            "id": 42,
            "location_id": 10,
            "filename": "photo.jpg",
            "file_path": "locations/10/photo.jpg",
            "url": "/uploads/locations/10/photo.jpg",
            "alt_text": "Caption",
            "is_featured": True,
            "sort_order": 1,
            "created_at": datetime(2025, 1, 15, 12, 0, 0),
        }
        obj = LocationImageRead(**data)
        out = obj.model_dump()
        assert out["id"] == 42
        assert out["location_id"] == 10


class TestLocationImageReadEmbedded:
    """Embedded schema omits id and location_id for use in location responses."""

    def test_does_not_have_id_or_location_id_fields(self) -> None:
        fields = set(LocationImageReadEmbedded.model_fields.keys())
        assert "id" not in fields
        assert "location_id" not in fields

    def test_has_required_embedding_fields(self) -> None:
        fields = set(LocationImageReadEmbedded.model_fields.keys())
        assert fields == {
            "filename",
            "file_path",
            "url",
            "alt_text",
            "is_featured",
            "sort_order",
            "created_at",
        }

    def test_roundtrip_excludes_id_and_location_id(self) -> None:
        data = {
            "filename": "photo.jpg",
            "file_path": "locations/10/photo.jpg",
            "url": "/uploads/locations/10/photo.jpg",
            "alt_text": None,
            "is_featured": True,
            "sort_order": 0,
            "created_at": datetime(2025, 1, 15, 12, 0, 0),
        }
        obj = LocationImageReadEmbedded(**data)
        out = obj.model_dump()
        assert "id" not in out
        assert "location_id" not in out
        assert out["filename"] == "photo.jpg"
        assert out["url"] == "/uploads/locations/10/photo.jpg"
