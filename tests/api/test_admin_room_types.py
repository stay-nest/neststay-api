"""Tests for admin room type API endpoints."""

from fastapi.testclient import TestClient


class TestListRoomTypes:
    """Tests for GET /admin/room-types/ endpoint."""

    def test_list_room_types_empty(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        """Should return empty list when no room types exist."""
        response = client.get("/admin/room-types/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    def test_list_room_types_without_auth_returns_401(
        self, client: TestClient
    ) -> None:
        """Should return 401 when not authenticated."""
        response = client.get("/admin/room-types/")
        assert response.status_code == 401

    def test_list_room_types_with_data(
        self, client: TestClient, sample_room_type_data: dict, auth_headers: dict
    ) -> None:
        """Should return list of room types."""
        client.post(
            "/admin/room-types/",
            json=sample_room_type_data,
            headers=auth_headers,
        )

        response = client.get("/admin/room-types/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["items"][0]["name"] == sample_room_type_data["name"]
        assert data["items"][0]["location_id"] == sample_room_type_data["location_id"]

    def test_list_room_types_pagination(
        self, client: TestClient, db_hotel_and_location: dict, auth_headers: dict
    ) -> None:
        """Should paginate results correctly."""
        location_id = db_hotel_and_location["location"].id
        for i in range(3):
            client.post(
                "/admin/room-types/",
                json={
                    "location_id": location_id,
                    "name": f"Room Type {i}",
                    "base_price": "99.99",
                },
                headers=auth_headers,
            )

        response = client.get(
            "/admin/room-types/?page=1&page_size=2",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["page_size"] == 2


class TestListRoomTypesByLocation:
    """Tests for GET /admin/room-types/location/{location_id} endpoint."""

    def test_list_by_location_success(
        self,
        client: TestClient,
        sample_room_type_data: dict,
        db_hotel_and_location: dict,
        auth_headers: dict,
    ) -> None:
        """Should return room types for the given location."""
        client.post(
            "/admin/room-types/",
            json=sample_room_type_data,
            headers=auth_headers,
        )
        location_id = db_hotel_and_location["location"].id

        response = client.get(
            f"/admin/room-types/location/{location_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == sample_room_type_data["name"]

    def test_list_by_location_not_found(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        """Should return 404 for non-existent location."""
        response = client.get(
            "/admin/room-types/location/99999",
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestCreateRoomType:
    """Tests for POST /admin/room-types/ endpoint."""

    def test_create_room_type_success(
        self,
        client: TestClient,
        sample_room_type_data: dict,
        db_hotel_and_location: dict,
        auth_headers: dict,
    ) -> None:
        """Should create a room type successfully."""
        response = client.post(
            "/admin/room-types/",
            json=sample_room_type_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_room_type_data["name"]
        assert data["location_id"] == sample_room_type_data["location_id"]
        assert "hotel_id" in data
        assert data["hotel_id"] == db_hotel_and_location["hotel"].id
        assert "slug" in data
        assert data["slug"].startswith("deluxe-suite-")
        assert data["is_active"] is True
        assert data["base_price"] == "149.99"
        assert data["total_inventory"] == 10
        assert data["max_occupancy"] == 4

    def test_create_room_type_derives_hotel_id(
        self,
        client: TestClient,
        sample_room_type_data: dict,
        db_hotel_and_location: dict,
        auth_headers: dict,
    ) -> None:
        """Should auto-derive hotel_id from location."""
        response = client.post(
            "/admin/room-types/",
            json=sample_room_type_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        expected_hotel_id = db_hotel_and_location["hotel"].id
        assert data["hotel_id"] == expected_hotel_id

    def test_create_room_type_location_not_found(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        """Should return 404 when location does not exist."""
        response = client.post(
            "/admin/room-types/",
            json={
                "location_id": 99999,
                "name": "Deluxe Suite",
                "base_price": "99.99",
            },
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_create_room_type_missing_required_field(
        self, client: TestClient, db_hotel_and_location: dict, auth_headers: dict
    ) -> None:
        """Should return 422 when location_id is missing."""
        response = client.post(
            "/admin/room-types/",
            json={
                "name": "Deluxe Suite",
                "base_price": "99.99",
            },
            headers=auth_headers,
        )

        assert response.status_code == 422


class TestGetRoomType:
    """Tests for GET /admin/room-types/{slug} endpoint."""

    def test_get_room_type_success(
        self,
        client: TestClient,
        sample_room_type_data: dict,
        auth_headers: dict,
    ) -> None:
        """Should return room type by slug."""
        create_response = client.post(
            "/admin/room-types/",
            json=sample_room_type_data,
            headers=auth_headers,
        )
        slug = create_response.json()["slug"]

        response = client.get(f"/admin/room-types/{slug}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == slug
        assert data["name"] == sample_room_type_data["name"]

    def test_get_room_type_not_found(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        """Should return 404 for non-existent room type."""
        response = client.get(
            "/admin/room-types/non-existent-slug",
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestUpdateRoomType:
    """Tests for PUT /admin/room-types/{slug} endpoint."""

    def test_update_room_type_success(
        self,
        client: TestClient,
        sample_room_type_data: dict,
        auth_headers: dict,
    ) -> None:
        """Should update room type successfully."""
        create_response = client.post(
            "/admin/room-types/",
            json=sample_room_type_data,
            headers=auth_headers,
        )
        slug = create_response.json()["slug"]

        response = client.put(
            f"/admin/room-types/{slug}",
            json={"name": "Updated Room Name", "base_price": "199.99"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Room Name"
        assert data["base_price"] == "199.99"
        assert data["slug"] == slug

    def test_update_room_type_partial(
        self,
        client: TestClient,
        sample_room_type_data: dict,
        auth_headers: dict,
    ) -> None:
        """Should allow partial updates."""
        create_response = client.post(
            "/admin/room-types/",
            json=sample_room_type_data,
            headers=auth_headers,
        )
        slug = create_response.json()["slug"]

        response = client.put(
            f"/admin/room-types/{slug}",
            json={"description": "New description"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "New description"
        assert data["name"] == sample_room_type_data["name"]

    def test_update_room_type_not_found(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        """Should return 404 for non-existent room type."""
        response = client.put(
            "/admin/room-types/non-existent-slug",
            json={"name": "Updated Name"},
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestDeleteRoomType:
    """Tests for DELETE /admin/room-types/{slug} endpoint."""

    def test_delete_room_type_success(
        self,
        client: TestClient,
        sample_room_type_data: dict,
        auth_headers: dict,
    ) -> None:
        """Should soft delete room type successfully."""
        create_response = client.post(
            "/admin/room-types/",
            json=sample_room_type_data,
            headers=auth_headers,
        )
        slug = create_response.json()["slug"]

        response = client.delete(
            f"/admin/room-types/{slug}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        get_response = client.get(
            f"/admin/room-types/{slug}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    def test_delete_room_type_not_found(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        """Should return 404 for non-existent room type."""
        response = client.delete(
            "/admin/room-types/non-existent-slug",
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_deleted_room_type_not_in_list(
        self,
        client: TestClient,
        sample_room_type_data: dict,
        auth_headers: dict,
    ) -> None:
        """Soft-deleted room type should not appear in listings."""
        create_response = client.post(
            "/admin/room-types/",
            json=sample_room_type_data,
            headers=auth_headers,
        )
        slug = create_response.json()["slug"]
        client.delete(
            f"/admin/room-types/{slug}",
            headers=auth_headers,
        )

        response = client.get("/admin/room-types/", headers=auth_headers)
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
