"""Tests for guest API endpoints."""

from fastapi.testclient import TestClient


class TestRegisterGuest:
    """Tests for POST /guest/register endpoint."""

    def test_register_by_phone_success(
        self, client: TestClient, sample_guest_register_phone: dict
    ):
        """Should register a guest by phone successfully."""
        response = client.post("/guest/register", json=sample_guest_register_phone)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_guest_register_phone["name"]
        assert data["phone_number"] == sample_guest_register_phone["phone_number"]
        assert data["email"] is None
        assert data["is_active"] is True
        assert "id" in data

    def test_register_by_email_success(
        self, client: TestClient, sample_guest_register_email: dict
    ):
        """Should register a guest by email successfully."""
        response = client.post("/guest/register", json=sample_guest_register_email)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_guest_register_email["name"]
        assert data["email"] == sample_guest_register_email["email"]
        assert data["is_active"] is True
        assert "id" in data
        # Service uses placeholder phone for email flow
        assert "email-" in data["phone_number"]

    def test_register_duplicate_phone_returns_409(
        self, client: TestClient, sample_guest_register_phone: dict
    ):
        """Should return 409 when phone number already registered."""
        client.post("/guest/register", json=sample_guest_register_phone)
        response = client.post("/guest/register", json=sample_guest_register_phone)

        assert response.status_code == 409

    def test_register_duplicate_email_returns_409(
        self, client: TestClient, sample_guest_register_email: dict
    ):
        """Should return 409 when email already registered."""
        client.post("/guest/register", json=sample_guest_register_email)
        response = client.post("/guest/register", json=sample_guest_register_email)

        assert response.status_code == 409

    def test_register_email_without_password_returns_422(self, client: TestClient):
        """Should return 422 when email provided without password."""
        response = client.post(
            "/guest/register",
            json={"name": "Guest", "email": "guest@test.com"},
        )

        assert response.status_code == 422

    def test_register_both_flows_prefers_phone(self, client: TestClient):
        """When both phone and email+password sent, phone flow is used."""
        payload = {
            "name": "Dual Guest",
            "phone_number": "+1999999999",
            "email": "dual@test.com",
            "password": "secret",
        }
        response = client.post("/guest/register", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["phone_number"] == "+1999999999"
        assert data["email"] == "dual@test.com"


class TestGetGuestByPhone:
    """Tests for GET /guest/by-phone/{phone_number} endpoint."""

    def test_get_by_phone_success(
        self, client: TestClient, created_guest: dict, sample_guest_register_phone: dict
    ):
        """Should return guest by phone number."""
        phone = sample_guest_register_phone["phone_number"]
        response = client.get(f"/guest/by-phone/{phone}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_guest["id"]
        assert data["phone_number"] == phone

    def test_get_by_phone_not_found(self, client: TestClient):
        """Should return 404 for unknown phone."""
        response = client.get("/guest/by-phone/+0000000000")

        assert response.status_code == 404


class TestGetGuestByEmail:
    """Tests for GET /guest/by-email/{email} endpoint."""

    def test_get_by_email_success(
        self, client: TestClient, sample_guest_register_email: dict
    ):
        """Should return guest by email."""
        client.post("/guest/register", json=sample_guest_register_email)
        email = sample_guest_register_email["email"]
        response = client.get(f"/guest/by-email/{email}")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == email

    def test_get_by_email_not_found(self, client: TestClient):
        """Should return 404 for unknown email."""
        response = client.get("/guest/by-email/unknown@test.com")

        assert response.status_code == 404


class TestGetGuestById:
    """Tests for GET /guest/{guest_id} endpoint."""

    def test_get_by_id_success(self, client: TestClient, created_guest: dict):
        """Should return guest by ID."""
        guest_id = created_guest["id"]
        response = client.get(f"/guest/{guest_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == guest_id
        assert data["name"] == created_guest["name"]

    def test_get_by_id_not_found(self, client: TestClient):
        """Should return 404 for non-existent guest ID."""
        response = client.get("/guest/99999")

        assert response.status_code == 404


class TestUpdateGuest:
    """Tests for PUT /guest/{guest_id} endpoint."""

    def test_update_guest_success(self, client: TestClient, created_guest: dict):
        """Should update guest successfully."""
        guest_id = created_guest["id"]
        update_data = {"name": "Updated Guest Name"}

        response = client.put(f"/guest/{guest_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Guest Name"
        assert data["id"] == guest_id

    def test_update_guest_partial(self, client: TestClient, created_guest: dict):
        """Should allow partial updates."""
        guest_id = created_guest["id"]
        update_data = {"email": "updated@test.com"}

        response = client.put(f"/guest/{guest_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated@test.com"
        assert data["name"] == created_guest["name"]

    def test_update_guest_not_found(self, client: TestClient):
        """Should return 404 for non-existent guest."""
        response = client.put(
            "/guest/99999",
            json={"name": "Updated Name"},
        )

        assert response.status_code == 404


class TestDeleteGuestPublic:
    """Tests for DELETE /guest/{guest_id} endpoint (public)."""

    def test_delete_guest_success(self, client: TestClient, created_guest: dict):
        """Should soft delete guest successfully."""
        guest_id = created_guest["id"]

        response = client.delete(f"/guest/{guest_id}")

        assert response.status_code == 204

        get_response = client.get(f"/guest/{guest_id}")
        assert get_response.status_code == 404

    def test_delete_guest_not_found(self, client: TestClient):
        """Should return 404 for non-existent guest."""
        response = client.delete("/guest/99999")

        assert response.status_code == 404


class TestAdminListGuests:
    """Tests for GET /admin/guest/ endpoint."""

    def test_list_guests_empty(self, client: TestClient):
        """Should return empty list when no guests exist."""
        response = client.get("/admin/guest/")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    def test_list_guests_with_data(
        self, client: TestClient, sample_guest_register_phone: dict
    ):
        """Should return list of guests."""
        client.post("/guest/register", json=sample_guest_register_phone)

        response = client.get("/admin/guest/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["items"][0]["name"] == sample_guest_register_phone["name"]

    def test_list_guests_pagination(
        self, client: TestClient, sample_guest_register_phone: dict
    ):
        """Should paginate results correctly."""
        for i in range(3):
            client.post(
                "/guest/register",
                json={
                    "name": f"Guest {i}",
                    "phone_number": f"+1234567890{i}",
                },
            )

        response = client.get("/admin/guest/?page=1&page_size=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["page_size"] == 2

        response = client.get("/admin/guest/?page=2&page_size=2")
        data = response.json()
        assert len(data["items"]) == 1
        assert data["page"] == 2


class TestAdminDeleteGuest:
    """Tests for DELETE /admin/guest/{guest_id} endpoint."""

    def test_admin_delete_guest_success(
        self, client: TestClient, created_guest: dict
    ):
        """Should soft delete guest successfully."""
        guest_id = created_guest["id"]

        response = client.delete(f"/admin/guest/{guest_id}")

        assert response.status_code == 204

        get_response = client.get(f"/guest/{guest_id}")
        assert get_response.status_code == 404

    def test_admin_delete_guest_not_found(self, client: TestClient):
        """Should return 404 for non-existent guest."""
        response = client.delete("/admin/guest/99999")

        assert response.status_code == 404
