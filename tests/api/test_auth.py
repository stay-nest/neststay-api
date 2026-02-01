"""Tests for auth API endpoints."""

from datetime import datetime, timezone, timedelta

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from config import settings


@pytest.fixture
def auth_guest(client: TestClient, sample_guest_register_email: dict) -> dict:
    """Create a guest with email+password for auth tests."""
    response = client.post("/guest/register", json=sample_guest_register_email)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def auth_tokens(client: TestClient, auth_guest: dict, sample_guest_register_email: dict) -> dict:
    """Login and return token response."""
    response = client.post(
        "/auth/login",
        json={
            "email": sample_guest_register_email["email"],
            "password": sample_guest_register_email["password"],
        },
    )
    assert response.status_code == 200
    return response.json()


class TestLogin:
    """Tests for POST /auth/login."""

    def test_login_valid_credentials_returns_tokens(
        self,
        client: TestClient,
        auth_guest: dict,
        sample_guest_register_email: dict,
    ):
        """Login with valid credentials returns 200 and access/refresh tokens."""
        response = client.post(
            "/auth/login",
            json={
                "email": sample_guest_register_email["email"],
                "password": sample_guest_register_email["password"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_email_returns_401(
        self, client: TestClient, auth_guest: dict, sample_guest_register_email: dict
    ):
        """Login with invalid email returns 401."""
        response = client.post(
            "/auth/login",
            json={
                "email": "nonexistent@test.com",
                "password": sample_guest_register_email["password"],
            },
        )
        assert response.status_code == 401

    def test_login_invalid_password_returns_401(
        self, client: TestClient, auth_guest: dict, sample_guest_register_email: dict
    ):
        """Login with invalid password returns 401."""
        response = client.post(
            "/auth/login",
            json={
                "email": sample_guest_register_email["email"],
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401


class TestRefresh:
    """Tests for POST /auth/refresh."""

    def test_refresh_valid_token_returns_new_access_token(
        self, client: TestClient, auth_tokens: dict, auth_guest: dict
    ):
        """Refresh with valid token returns 200 and usable access_token."""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": auth_tokens["refresh_token"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["refresh_token"] == auth_tokens["refresh_token"]
        assert data["token_type"] == "bearer"
        # Refreshed access token must work for /auth/me
        me_response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {data['access_token']}"},
        )
        assert me_response.status_code == 200
        assert me_response.json()["id"] == auth_guest["id"]

    def test_refresh_expired_token_returns_401(self, client: TestClient, auth_guest: dict):
        """Refresh with expired token returns 401."""
        expired_payload = {
            "sub": str(auth_guest["id"]),
            "exp": datetime.now(timezone.utc) - timedelta(days=1),
        }
        expired_token = jwt.encode(
            expired_payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": expired_token},
        )
        assert response.status_code == 401

    def test_refresh_invalid_token_returns_401(self, client: TestClient):
        """Refresh with invalid token returns 401."""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid.jwt.token"},
        )
        assert response.status_code == 401


class TestMe:
    """Tests for GET /auth/me."""

    def test_me_with_valid_token_returns_guest(
        self, client: TestClient, auth_tokens: dict, auth_guest: dict
    ):
        """GET /auth/me with valid Bearer returns 200 and GuestRead."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == auth_guest["id"]
        assert data["email"] == auth_guest["email"]
        assert data["name"] == auth_guest["name"]
        assert "password" not in data

    def test_me_without_token_returns_401(self, client: TestClient):
        """GET /auth/me without token returns 401."""
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_me_with_expired_token_returns_401(
        self, client: TestClient, auth_guest: dict
    ):
        """GET /auth/me with expired access token returns 401."""
        expired_payload = {
            "sub": str(auth_guest["id"]),
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        }
        expired_token = jwt.encode(
            expired_payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401
