"""Schemas for request/response validation."""

from .guest_schema import (
    GuestCreate,
    GuestIndexResponse,
    GuestRead,
    GuestUpdate,
)
from .location_schema import (
    LocationCreate,
    LocationIndexResponse,
    LocationRead,
    LocationUpdate,
)

__all__ = [
    "GuestCreate",
    "GuestIndexResponse",
    "GuestRead",
    "GuestUpdate",
    "LocationCreate",
    "LocationIndexResponse",
    "LocationRead",
    "LocationUpdate",
]
