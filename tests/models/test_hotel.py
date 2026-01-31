"""Unit tests for Hotel model.

Assert table name, column attributes (types, primary_key, unique, defaults),
and relationship so that any change in the model breaks a test if not covered.
"""

from __future__ import annotations

import pytest
from sqlalchemy import Boolean, Column, DateTime, Integer, inspect as sa_inspect
from sqlmodel.sql.sqltypes import AutoString

from app.models.hotel import Hotel


class TestHotelTableName:
    """Assert correct table name."""

    def test_table_name_is_hotels(self) -> None:
        assert Hotel.__tablename__ == "hotels"


class TestHotelColumns:
    """Assert correct column definitions (name, type, primary_key, unique, default)."""

    @pytest.fixture
    def columns(self) -> dict[str, Column]:
        return {c.name: c for c in Hotel.__table__.columns}

    def test_has_expected_columns(self, columns: dict) -> None:
        expected = {
            "id",
            "name",
            "slug",
            "description",
            "contact_phone",
            "is_active",
            "contact_email",
            "location_count",
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

    def test_slug_is_unique_string(self, columns: dict) -> None:
        slug_col = columns["slug"]
        assert type(slug_col.type) is AutoString
        assert slug_col.unique
        assert not slug_col.nullable

    def test_description_is_nullable_string(self, columns: dict) -> None:
        desc_col = columns["description"]
        assert type(desc_col.type) is AutoString
        assert desc_col.nullable

    def test_contact_phone_is_required_string(self, columns: dict) -> None:
        phone_col = columns["contact_phone"]
        assert type(phone_col.type) is AutoString
        assert not phone_col.nullable

    def test_is_active_is_boolean_with_default_true(self, columns: dict) -> None:
        active_col = columns["is_active"]
        assert type(active_col.type) is Boolean
        assert active_col.default is not None
        assert active_col.default.arg is True
        assert not active_col.nullable

    def test_contact_email_is_nullable_string(self, columns: dict) -> None:
        email_col = columns["contact_email"]
        assert type(email_col.type) is AutoString
        assert email_col.nullable

    def test_location_count_is_integer_with_default(self, columns: dict) -> None:
        count_col = columns["location_count"]
        assert type(count_col.type) is Integer
        assert count_col.default is not None
        assert not count_col.nullable

    def test_deleted_at_is_nullable_datetime(self, columns: dict) -> None:
        deleted_col = columns["deleted_at"]
        assert type(deleted_col.type) is DateTime
        assert deleted_col.nullable


class TestHotelModelFields:
    """Assert Pydantic/model field metadata (types and defaults) for API."""

    def test_id_field_is_optional_int_primary_key(self) -> None:
        f = Hotel.model_fields["id"]
        assert f.annotation == int | None
        assert f.default is None
        # primary_key=True asserted in TestHotelColumns.test_id_is_integer_primary_key

    def test_name_field_is_required_str(self) -> None:
        f = Hotel.model_fields["name"]
        assert f.annotation is str
        assert f.is_required()

    def test_slug_field_is_required_str_unique(self) -> None:
        f = Hotel.model_fields["slug"]
        assert f.annotation is str
        assert f.is_required()
        # unique=True is asserted in TestHotelColumns.test_slug_is_unique_string

    def test_description_field_is_optional_str(self) -> None:
        f = Hotel.model_fields["description"]
        assert f.annotation == str | None
        assert not f.is_required()

    def test_contact_phone_field_is_required_str(self) -> None:
        f = Hotel.model_fields["contact_phone"]
        assert f.annotation is str
        assert f.is_required()

    def test_is_active_field_default_true(self) -> None:
        f = Hotel.model_fields["is_active"]
        assert f.annotation is bool
        assert f.default is True

    def test_contact_email_field_is_optional_str(self) -> None:
        f = Hotel.model_fields["contact_email"]
        assert f.annotation == str | None
        assert not f.is_required()

    def test_location_count_field_default_zero(self) -> None:
        f = Hotel.model_fields["location_count"]
        assert f.annotation is int
        assert f.default == 0

    def test_deleted_at_field_is_optional_datetime(self) -> None:
        f = Hotel.model_fields["deleted_at"]
        assert "datetime" in str(f.annotation).lower() or "datetime" in str(
            f.annotation
        )
        assert not f.is_required()


class TestHotelRelationship:
    """Assert relationship to Location (back_populates)."""

    def test_has_locations_relationship(self) -> None:
        mapper = sa_inspect(Hotel)
        rels = {r.key: r for r in mapper.relationships}
        assert "locations" in rels

    def test_locations_relationship_back_populates_hotel(self) -> None:
        mapper = sa_inspect(Hotel)
        rel = next(r for r in mapper.relationships if r.key == "locations")
        assert rel.back_populates == "hotel"

    def test_locations_relationship_target_is_location_entity(self) -> None:
        mapper = sa_inspect(Hotel)
        rel = next(r for r in mapper.relationships if r.key == "locations")
        assert rel.mapper.class_.__name__ == "Location"
