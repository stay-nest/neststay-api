"""Unit tests for Guest model.

Assert table name, column attributes (types, primary_key, unique, defaults),
and that the model has no relationships.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import Boolean, Column, DateTime, Integer, inspect as sa_inspect
from sqlmodel.sql.sqltypes import AutoString

from app.models.guest import Guest


class TestGuestTableName:
    """Assert correct table name."""

    def test_table_name_is_guests(self) -> None:
        assert Guest.__tablename__ == "guests"


class TestGuestColumns:
    """Assert correct column definitions (name, type, primary_key, unique, default)."""

    @pytest.fixture
    def columns(self) -> dict[str, Column]:
        return {c.name: c for c in Guest.__table__.columns}

    def test_has_expected_columns(self, columns: dict) -> None:
        expected = {
            "id",
            "name",
            "email",
            "phone_number",
            "password",
            "is_active",
            "created_at",
            "updated_at",
            "deleted_at",
        }
        assert set(columns.keys()) == expected

    def test_id_is_integer_primary_key(self, columns: dict) -> None:
        id_col = columns["id"]
        assert id_col.primary_key
        assert type(id_col.type) is Integer
        assert not id_col.nullable  # PK is NOT NULL at DB level (auto-increment)

    def test_name_is_required_string(self, columns: dict) -> None:
        name_col = columns["name"]
        assert type(name_col.type) is AutoString
        assert not name_col.nullable

    def test_email_is_nullable_string(self, columns: dict) -> None:
        email_col = columns["email"]
        assert type(email_col.type) is AutoString
        assert email_col.nullable

    def test_phone_number_is_unique_string(self, columns: dict) -> None:
        phone_col = columns["phone_number"]
        assert type(phone_col.type) is AutoString
        assert phone_col.unique
        assert not phone_col.nullable

    def test_password_is_nullable_string(self, columns: dict) -> None:
        password_col = columns["password"]
        assert type(password_col.type) is AutoString
        assert password_col.nullable

    def test_is_active_is_boolean_with_default_true(self, columns: dict) -> None:
        active_col = columns["is_active"]
        assert type(active_col.type) is Boolean
        assert active_col.default is not None
        assert active_col.default.arg is True
        assert not active_col.nullable

    def test_created_at_is_datetime(self, columns: dict) -> None:
        created_col = columns["created_at"]
        assert type(created_col.type) is DateTime
        assert not created_col.nullable

    def test_updated_at_is_datetime(self, columns: dict) -> None:
        updated_col = columns["updated_at"]
        assert type(updated_col.type) is DateTime
        assert not updated_col.nullable

    def test_deleted_at_is_nullable_datetime(self, columns: dict) -> None:
        deleted_col = columns["deleted_at"]
        assert type(deleted_col.type) is DateTime
        assert deleted_col.nullable


class TestGuestModelFields:
    """Assert Pydantic/model field metadata (types and defaults) for API."""

    def test_id_field_is_optional_int_primary_key(self) -> None:
        f = Guest.model_fields["id"]
        assert f.annotation == int | None
        assert f.default is None
        # primary_key=True asserted in TestGuestColumns.test_id_is_integer_primary_key

    def test_name_field_is_required_str(self) -> None:
        f = Guest.model_fields["name"]
        assert f.annotation is str
        assert f.is_required()

    def test_email_field_is_optional_str(self) -> None:
        f = Guest.model_fields["email"]
        assert f.annotation == str | None
        assert not f.is_required()

    def test_phone_number_field_is_required_str_unique(self) -> None:
        f = Guest.model_fields["phone_number"]
        assert f.annotation is str
        assert f.is_required()
        # unique=True is asserted in TestGuestColumns.test_phone_number_is_unique_string

    def test_password_field_is_optional_str(self) -> None:
        f = Guest.model_fields["password"]
        assert f.annotation == str | None
        assert not f.is_required()

    def test_is_active_field_default_true(self) -> None:
        f = Guest.model_fields["is_active"]
        assert f.annotation is bool
        assert f.default is True

    def test_created_at_field_has_default(self) -> None:
        f = Guest.model_fields["created_at"]
        assert "datetime" in str(f.annotation).lower() or "datetime" in str(
            f.annotation
        )
        assert not f.is_required()

    def test_updated_at_field_has_default(self) -> None:
        f = Guest.model_fields["updated_at"]
        assert "datetime" in str(f.annotation).lower() or "datetime" in str(
            f.annotation
        )
        assert not f.is_required()

    def test_deleted_at_field_is_optional_datetime(self) -> None:
        f = Guest.model_fields["deleted_at"]
        assert f.annotation == datetime | None
        assert not f.is_required()


class TestGuestRelationship:
    """Assert Guest relationships."""

    def test_has_bookings_relationship(self) -> None:
        relationships = sa_inspect(Guest).relationships
        names = {rel.key for rel in relationships}
        assert "bookings" in names
