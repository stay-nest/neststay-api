"""Tests for location image API endpoints."""

import tempfile

import pytest
from fastapi.testclient import TestClient

from app.routes.location_image import get_storage
from app.services.storage.local import LocalStorageService
from main import app

# Minimal valid JPEG (1x1 pixel)
MINIMAL_JPEG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n"
    b"\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d"
    b"\x1a\x1c\x1c $.' \",#\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c"
    b"\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c"
    b"\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\xff\xc0\x00\x0b\x08\x00"
    b"\x01\x00\x01\x01\x01\x00\x1f\x00\xff\xc4\x00\x1f\x00\x00\x01\x05"
    b"\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02"
    b"\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x0c\x03\x01\x00\x02"
    b"\x10\x03\x10\x00\x00\x01\x1f\x00\xff\xd9"
)


@pytest.fixture
def temp_upload_dir():
    """Create a temporary directory for uploads and override storage to use it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        app.dependency_overrides[get_storage] = lambda: LocalStorageService(tmpdir)
        yield tmpdir
    app.dependency_overrides.pop(get_storage, None)


class TestUploadImage:
    """Tests for POST /locations/{location_id}/images/."""

    def test_upload_without_auth_returns_401(self, client: TestClient, db_hotel_and_location: dict):
        """Upload without auth returns 401."""
        location_id = db_hotel_and_location["location"].id
        response = client.post(
            f"/locations/{location_id}/images/",
            files={"file": ("test.jpg", MINIMAL_JPEG, "image/jpeg")},
        )
        assert response.status_code == 401

    def test_upload_returns_201_and_response_has_url_and_path(
        self,
        client: TestClient,
        db_hotel_and_location: dict,
        temp_upload_dir: str,
        auth_headers: dict,
    ):
        """Upload image returns 201 and response includes url, file_path, is_featured."""
        location_id = db_hotel_and_location["location"].id
        response = client.post(
            f"/locations/{location_id}/images/",
            files={"file": ("test.jpg", MINIMAL_JPEG, "image/jpeg")},
            data={"alt_text": "A test image"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert "url" in data
        # Local storage may return full URL (APP_URL + /uploads/...) or path-only
        assert "/uploads/" in data["url"]
        assert "file_path" in data
        assert "locations" in data["file_path"] and str(location_id) in data["file_path"]
        assert data["filename"] == "test.jpg"
        assert data["alt_text"] == "A test image"
        assert data["is_featured"] is False
        assert data["location_id"] == location_id

    def test_upload_with_is_featured(
        self,
        client: TestClient,
        db_hotel_and_location: dict,
        temp_upload_dir: str,
        auth_headers: dict,
    ):
        """Upload with is_featured=true sets that image as featured."""
        location_id = db_hotel_and_location["location"].id
        response = client.post(
            f"/locations/{location_id}/images/",
            files={"file": ("photo.jpg", MINIMAL_JPEG, "image/jpeg")},
            data={"is_featured": "true"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["is_featured"] is True

    def test_upload_404_for_nonexistent_location(
        self,
        client: TestClient,
        temp_upload_dir: str,
        auth_headers: dict,
    ):
        """Upload returns 404 when location_id does not exist."""
        response = client.post(
            "/locations/99999/images/",
            files={"file": ("test.jpg", MINIMAL_JPEG, "image/jpeg")},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_upload_rejects_invalid_file_type(
        self,
        client: TestClient,
        db_hotel_and_location: dict,
        temp_upload_dir: str,
        auth_headers: dict,
    ):
        """Upload returns 400 for disallowed file type."""
        location_id = db_hotel_and_location["location"].id
        response = client.post(
            f"/locations/{location_id}/images/",
            files={"file": ("file.pdf", b"%PDF-1.4", "application/pdf")},
            headers=auth_headers,
        )
        assert response.status_code == 400


class TestListImages:
    """Tests for GET /locations/{location_id}/images/."""

    def test_list_without_auth_returns_401(self, client: TestClient, db_hotel_and_location: dict):
        """List without auth returns 401."""
        location_id = db_hotel_and_location["location"].id
        response = client.get(f"/locations/{location_id}/images/")
        assert response.status_code == 401

    def test_list_empty(self, client: TestClient, db_hotel_and_location: dict, auth_headers: dict):
        """List returns empty list when no images."""
        location_id = db_hotel_and_location["location"].id
        response = client.get(f"/locations/{location_id}/images/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_returns_uploaded_images(
        self,
        client: TestClient,
        db_hotel_and_location: dict,
        temp_upload_dir: str,
        auth_headers: dict,
    ):
        """List returns images with url after upload."""
        location_id = db_hotel_and_location["location"].id
        client.post(
            f"/locations/{location_id}/images/",
            files={"file": ("a.jpg", MINIMAL_JPEG, "image/jpeg")},
            headers=auth_headers,
        )
        response = client.get(f"/locations/{location_id}/images/", headers=auth_headers)
        assert response.status_code == 200
        items = response.json()
        assert len(items) == 1
        # Local storage may return full URL (APP_URL + /uploads/...) or path-only
        assert "/uploads/" in items[0]["url"]

    def test_list_404_for_nonexistent_location(self, client: TestClient, auth_headers: dict):
        """List returns 404 when location does not exist."""
        response = client.get("/locations/99999/images/", headers=auth_headers)
        assert response.status_code == 404


class TestSetFeatured:
    """Tests for POST /locations/{location_id}/images/{image_id}/featured."""

    def test_set_featured(
        self,
        client: TestClient,
        db_hotel_and_location: dict,
        temp_upload_dir: str,
        auth_headers: dict,
    ):
        """Setting featured updates the image and only one is featured."""
        location_id = db_hotel_and_location["location"].id
        r1 = client.post(
            f"/locations/{location_id}/images/",
            files={"file": ("1.jpg", MINIMAL_JPEG, "image/jpeg")},
            headers=auth_headers,
        )
        r2 = client.post(
            f"/locations/{location_id}/images/",
            files={"file": ("2.jpg", MINIMAL_JPEG, "image/jpeg")},
            data={"is_featured": "true"},
            headers=auth_headers,
        )
        assert r1.json()["is_featured"] is False
        assert r2.json()["is_featured"] is True
        image_id_1 = r1.json()["id"]
        response = client.post(
            f"/locations/{location_id}/images/{image_id_1}/featured",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["is_featured"] is True
        list_resp = client.get(f"/locations/{location_id}/images/", headers=auth_headers)
        featured = [i for i in list_resp.json() if i["is_featured"]]
        assert len(featured) == 1
        assert featured[0]["id"] == image_id_1

    def test_set_featured_404_for_wrong_image(
        self,
        client: TestClient,
        db_hotel_and_location: dict,
        temp_upload_dir: str,
        auth_headers: dict,
    ):
        """Set featured returns 404 when image_id does not exist."""
        location_id = db_hotel_and_location["location"].id
        response = client.post(
            f"/locations/{location_id}/images/99999/featured",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestUpdateImage:
    """Tests for PATCH /locations/{location_id}/images/{image_id}."""

    def test_update_alt_text_and_sort_order(
        self,
        client: TestClient,
        db_hotel_and_location: dict,
        temp_upload_dir: str,
        auth_headers: dict,
    ):
        """Update alt_text and sort_order."""
        location_id = db_hotel_and_location["location"].id
        upload = client.post(
            f"/locations/{location_id}/images/",
            files={"file": ("x.jpg", MINIMAL_JPEG, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload.json()["id"]
        response = client.patch(
            f"/locations/{location_id}/images/{image_id}",
            json={"alt_text": "Updated alt", "sort_order": 5},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["alt_text"] == "Updated alt"
        assert response.json()["sort_order"] == 5

    def test_update_404_for_nonexistent_image(
        self,
        client: TestClient,
        db_hotel_and_location: dict,
        auth_headers: dict,
    ):
        """Update returns 404 when image_id does not exist."""
        location_id = db_hotel_and_location["location"].id
        response = client.patch(
            f"/locations/{location_id}/images/99999",
            json={"alt_text": "x"},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestDeleteImage:
    """Tests for DELETE /locations/{location_id}/images/{image_id}."""

    def test_delete_returns_204(
        self,
        client: TestClient,
        db_hotel_and_location: dict,
        temp_upload_dir: str,
        auth_headers: dict,
    ):
        """Delete returns 204 and removes image from list."""
        location_id = db_hotel_and_location["location"].id
        upload = client.post(
            f"/locations/{location_id}/images/",
            files={"file": ("del.jpg", MINIMAL_JPEG, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload.json()["id"]
        response = client.delete(
            f"/locations/{location_id}/images/{image_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204
        list_resp = client.get(f"/locations/{location_id}/images/", headers=auth_headers)
        assert len(list_resp.json()) == 0

    def test_delete_404_for_nonexistent_image(
        self,
        client: TestClient,
        db_hotel_and_location: dict,
        auth_headers: dict,
    ):
        """Delete returns 404 when image_id does not exist."""
        location_id = db_hotel_and_location["location"].id
        response = client.delete(
            f"/locations/{location_id}/images/99999",
            headers=auth_headers,
        )
        assert response.status_code == 404
