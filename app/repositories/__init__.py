"""Repositories for single-table database operations."""

from .guest_repo import GuestRepository
from .location_repo import LocationRepository

__all__ = ["GuestRepository", "LocationRepository"]
