"""Unit tests for Location model.

Assert table name, column attributes (types, primary_key, unique, defaults),
and relationship so that any change in the model breaks a test if not covered.
"""

from __future__ import annotations

import pytest
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, inspect as sa_inspect
from sqlmodel.sql.sqltypes import AutoString

from app.models.location import Location


class TestLocationTableName:
    """Assert correct table name."""

    def test_table_name_is_locations(self) -> None:
        assert Location.__tablename__ == "locations"


class TestLocationColumns:
    """Assert correct column definitions (name, type, primary_key, unique, default)."""

    @pytest.fixture
    def columns(self) -> dict[str, Column]:
        return {c.name: c for c in Location.__table__.columns}

    def test_has_expected_columns(self, columns: dict) -> None:
        expected = {
            "id",
            "hotel_id",
            "name",
            "description",
            "slug",
            "address",
            "latitude",
            "longitude",
            "city",
            "state",
            "country",
            "contact_phone",
            "contact_email",
            "is_active",
            "deleted_at",
        }
        assert set(columns.keys()) == expected

    def test_id_is_integer_primary_key(self, columns: dict) -> None:
        id_col = columns["id"]
        assert id_col.primary_key
        assert type(id_col.type) is Integer
        assert not id_col.nullable  # PK is NOT NULL at DB level (auto-increment)

    def test_hotel_id_is_integer_foreign_key_indexed(self, columns: dict) -> None:
        hotel_id_col = columns["hotel_id"]
        assert type(hotel_id_col.type) is Integer
        assert not hotel_id_col.nullable
        assert hotel_id_col.foreign_keys
        assert hotel_id_col.index

    def test_name_is_required_string(self, columns: dict) -> None:
        name_col = columns["name"]
        assert type(name_col.type) is AutoString
        assert not name_col.nullable

    def test_description_is_nullable_string(self, columns: dict) -> None:
        desc_col = columns["description"]
        assert type(desc_col.type) is AutoString
        assert desc_col.nullable

    def test_slug_is_unique_string(self, columns: dict) -> None:
        slug_col = columns["slug"]
        assert type(slug_col.type) is AutoString
        assert slug_col.unique
        assert not slug_col.nullable

    def test_address_is_required_string(self, columns: dict) -> None:
        addr_col = columns["address"]
        assert type(addr_col.type) is AutoString
        assert not addr_col.nullable

    def test_latitude_is_nullable_float(self, columns: dict) -> None:
        lat_col = columns["latitude"]
        assert type(lat_col.type) is Float
        assert lat_col.nullable

    def test_longitude_is_nullable_float(self, columns: dict) -> None:
        lon_col = columns["longitude"]
        assert type(lon_col.type) is Float
        assert lon_col.nullable

    def test_city_is_required_string(self, columns: dict) -> None:
        city_col = columns["city"]
        assert type(city_col.type) is AutoString
        assert not city_col.nullable

    def test_state_is_required_string(self, columns: dict) -> None:
        state_col = columns["state"]
        assert type(state_col.type) is AutoString
        assert not state_col.nullable

    def test_country_is_required_string(self, columns: dict) -> None:
        country_col = columns["country"]
        assert type(country_col.type) is AutoString
        assert not country_col.nullable

    def test_contact_phone_is_required_string(self, columns: dict) -> None:
        phone_col = columns["contact_phone"]
        assert type(phone_col.type) is AutoString
        assert not phone_col.nullable

    def test_contact_email_is_nullable_string(self, columns: dict) -> None:
        email_col = columns["contact_email"]
        assert type(email_col.type) is AutoString
        assert email_col.nullable

    def test_is_active_is_boolean_with_default_true(self, columns: dict) -> None:
        active_col = columns["is_active"]
        assert type(active_col.type) is Boolean
        assert active_col.default is not None
        assert active_col.default.arg is True
        assert not active_col.nullable

    def test_deleted_at_is_nullable_datetime(self, columns: dict) -> None:
        deleted_col = columns["deleted_at"]
        assert type(deleted_col.type) is DateTime
        assert deleted_col.nullable


class TestLocationModelFields:
    """Assert Pydantic/model field metadata (types and defaults) for API."""

    def test_id_field_is_optional_int_primary_key(self) -> None:
        f = Location.model_fields["id"]
        assert f.annotation == int | None
        assert f.default is None
        # primary_key=True asserted in TestLocationColumns.test_id_is_primary_key

    def test_hotel_id_field_is_required_int(self) -> None:
        f = Location.model_fields["hotel_id"]
        assert f.annotation is int
        assert f.is_required()

    def test_name_field_is_required_str(self) -> None:
        f = Location.model_fields["name"]
        assert f.annotation is str
        assert f.is_required()

    def test_description_field_is_optional_str(self) -> None:
        f = Location.model_fields["description"]
        assert f.annotation == str | None
        assert not f.is_required()

    def test_slug_field_is_required_str_unique(self) -> None:
        f = Location.model_fields["slug"]
        assert f.annotation is str
        assert f.is_required()
        # unique=True is asserted in TestLocationColumns.test_slug_is_unique_string

    def test_address_field_is_required_str(self) -> None:
        f = Location.model_fields["address"]
        assert f.annotation is str
        assert f.is_required()

    def test_latitude_field_is_optional_float(self) -> None:
        f = Location.model_fields["latitude"]
        assert f.annotation == float | None
        assert not f.is_required()

    def test_longitude_field_is_optional_float(self) -> None:
        f = Location.model_fields["longitude"]
        assert f.annotation == float | None
        assert not f.is_required()

    def test_city_field_is_required_str(self) -> None:
        f = Location.model_fields["city"]
        assert f.annotation is str
        assert f.is_required()

    def test_state_field_is_required_str(self) -> None:
        f = Location.model_fields["state"]
        assert f.annotation is str
        assert f.is_required()

    def test_country_field_is_required_str(self) -> None:
        f = Location.model_fields["country"]
        assert f.annotation is str
        assert f.is_required()

    def test_contact_phone_field_is_required_str(self) -> None:
        f = Location.model_fields["contact_phone"]
        assert f.annotation is str
        assert f.is_required()

    def test_contact_email_field_is_optional_str(self) -> None:
        f = Location.model_fields["contact_email"]
        assert f.annotation == str | None
        assert not f.is_required()

    def test_is_active_field_default_true(self) -> None:
        f = Location.model_fields["is_active"]
        assert f.annotation is bool
        assert f.default is True

    def test_deleted_at_field_is_optional_datetime(self) -> None:
        f = Location.model_fields["deleted_at"]
        assert "datetime" in str(f.annotation).lower() or "datetime" in str(
            f.annotation
        )
        assert not f.is_required()


class TestLocationRelationship:
    """Assert relationship to Hotel (back_populates)."""

    def test_has_hotel_relationship(self) -> None:
        mapper = sa_inspect(Location)
        rels = {r.key: r for r in mapper.relationships}
        assert "hotel" in rels

    def test_hotel_relationship_back_populates_locations(self) -> None:
        mapper = sa_inspect(Location)
        rel = next(r for r in mapper.relationships if r.key == "hotel")
        assert rel.back_populates == "locations"

    def test_hotel_relationship_target_is_hotel_entity(self) -> None:
        mapper = sa_inspect(Location)
        rel = next(r for r in mapper.relationships if r.key == "hotel")
        assert rel.mapper.class_.__name__ == "Hotel"


class TestLocationImagesRelationship:
    """Assert relationship to LocationImage (images list)."""

    def test_has_images_relationship(self) -> None:
        mapper = sa_inspect(Location)
        rels = {r.key: r for r in mapper.relationships}
        assert "images" in rels

    def test_images_relationship_back_populates_location(self) -> None:
        mapper = sa_inspect(Location)
        rel = next(r for r in mapper.relationships if r.key == "images")
        assert rel.back_populates == "location"

    def test_images_relationship_target_is_location_image_entity(self) -> None:
        mapper = sa_inspect(Location)
        rel = next(r for r in mapper.relationships if r.key == "images")
        assert rel.mapper.class_.__name__ == "LocationImage"


class TestLocationFeaturedImageRelationship:
    """Assert filtered featured_image relationship (single image where is_featured=True)."""

    def test_has_featured_image_relationship(self) -> None:
        mapper = sa_inspect(Location)
        rels = {r.key: r for r in mapper.relationships}
        assert "featured_image" in rels

    def test_featured_image_relationship_is_viewonly(self) -> None:
        mapper = sa_inspect(Location)
        rel = next(r for r in mapper.relationships if r.key == "featured_image")
        assert rel.viewonly is True

    def test_featured_image_relationship_uselist_false(self) -> None:
        mapper = sa_inspect(Location)
        rel = next(r for r in mapper.relationships if r.key == "featured_image")
        assert rel.uselist is False

    def test_featured_image_relationship_lazy_selectin(self) -> None:
        mapper = sa_inspect(Location)
        rel = next(r for r in mapper.relationships if r.key == "featured_image")
        assert str(rel.lazy) == "selectin"

    def test_featured_image_relationship_target_is_location_image_entity(self) -> None:
        mapper = sa_inspect(Location)
        rel = next(r for r in mapper.relationships if r.key == "featured_image")
        assert rel.mapper.class_.__name__ == "LocationImage"
