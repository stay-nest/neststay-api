"""RoomDateInventory repository for single-table database operations."""

from datetime import date, timedelta

from sqlmodel import Session, select

from app.models.room_date_inventory import RoomDateInventory


class RoomDateInventoryRepository:
    """Repository for RoomDateInventory entity operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def ensure_rows_exist(
        self,
        room_type_id: int,
        start_date: date,
        end_date: date,
        total_rooms: int,
    ) -> None:
        """
        Lazy creation: insert missing rows for the date range.

        start_date is inclusive, end_date is exclusive.
        Existing rows are left unchanged (total_rooms not updated).

        Args:
            room_type_id: The room type ID
            start_date: First date (inclusive)
            end_date: Last date (exclusive)
            total_rooms: Value for total_rooms on new rows
        """
        if start_date >= end_date:
            return
        # Find existing (room_type_id, date) in range
        statement = (
            select(RoomDateInventory.date)
            .where(RoomDateInventory.room_type_id == room_type_id)
            .where(RoomDateInventory.date >= start_date)
            .where(RoomDateInventory.date < end_date)
        )
        result = self.session.exec(statement).all()
        existing_dates = {(row[0] if isinstance(row, tuple) else row) for row in result}
        # Insert missing dates
        current = start_date
        while current < end_date:
            if current not in existing_dates:
                self.session.add(
                    RoomDateInventory(
                        room_type_id=room_type_id,
                        date=current,
                        total_rooms=total_rooms,
                        booked_count=0,
                    )
                )
            current += timedelta(days=1)

    def get_for_date_range_with_lock(
        self,
        room_type_id: int,
        start_date: date,
        end_date: date,
    ) -> list[RoomDateInventory]:
        """
        Load inventory rows for the date range with row-level lock (FOR UPDATE).

        start_date is inclusive, end_date is exclusive.
        SQLite ignores FOR UPDATE; MySQL locks the rows until commit.

        Args:
            room_type_id: The room type ID
            start_date: First date (inclusive)
            end_date: Last date (exclusive)

        Returns:
            List of RoomDateInventory rows, ordered by date
        """
        if start_date >= end_date:
            return []
        statement = (
            select(RoomDateInventory)
            .where(RoomDateInventory.room_type_id == room_type_id)
            .where(RoomDateInventory.date >= start_date)
            .where(RoomDateInventory.date < end_date)
            .order_by(RoomDateInventory.date)
            .with_for_update()
        )
        return list(self.session.exec(statement).all())

    def check_availability(
        self,
        room_type_id: int,
        start_date: date,
        end_date: date,
        num_rooms: int,
    ) -> tuple[bool, int]:
        """
        Check if num_rooms are available for every night in the range (read-only).

        start_date is inclusive, end_date is exclusive.
        If no inventory rows exist for the range, min_rooms_available is 0.

        Args:
            room_type_id: The room type ID
            start_date: First date (inclusive)
            end_date: Last date (exclusive)
            num_rooms: Number of rooms required

        Returns:
            (is_available, min_rooms_available)
        """
        if start_date >= end_date:
            return (True, 0)
        statement = (
            select(RoomDateInventory)
            .where(RoomDateInventory.room_type_id == room_type_id)
            .where(RoomDateInventory.date >= start_date)
            .where(RoomDateInventory.date < end_date)
        )
        rows = list(self.session.exec(statement).all())
        if not rows:
            return (False, 0)
        min_available = min(row.total_rooms - row.booked_count for row in rows)
        return (min_available >= num_rooms, min_available)

    def increment_booked(self, rows: list[RoomDateInventory], count: int) -> None:
        """
        Increment booked_count for each row by count.

        Args:
            rows: Inventory rows to update
            count: Amount to add to booked_count
        """
        for row in rows:
            row.booked_count += count
        self.session.add_all(rows)

    def decrement_booked(
        self,
        room_type_id: int,
        start_date: date,
        end_date: date,
        count: int,
    ) -> None:
        """
        Decrement booked_count for each date in range by count (no lower than 0).

        start_date is inclusive, end_date is exclusive.

        Args:
            room_type_id: The room type ID
            start_date: First date (inclusive)
            end_date: Last date (exclusive)
            count: Amount to subtract from booked_count
        """
        if start_date >= end_date:
            return
        statement = (
            select(RoomDateInventory)
            .where(RoomDateInventory.room_type_id == room_type_id)
            .where(RoomDateInventory.date >= start_date)
            .where(RoomDateInventory.date < end_date)
        )
        rows = list(self.session.exec(statement).all())
        for row in rows:
            row.booked_count = max(0, row.booked_count - count)
        self.session.add_all(rows)
