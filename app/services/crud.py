"""Database operations used by API routers and business services."""

from datetime import datetime
import sqlite3
from typing import Any

from app.core.security import hash_password
from app.schemas import (
    BookingCreate,
    BookingUpdate,
    EquipmentCreate,
    EquipmentUpdate,
    RoomCreate,
    RoomUpdate,
    UserCreate,
)


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    """Convert a SQLite row to a regular dictionary."""

    return dict(row) if row is not None else None


def create_user(db: sqlite3.Connection, user: UserCreate) -> dict[str, Any]:
    """Create a user and return the public database row."""

    cursor = db.execute(
        """
        INSERT INTO users (email, full_name, hashed_password, role)
        VALUES (?, ?, ?, ?)
        """,
        (user.email, user.full_name, hash_password(user.password), user.role.value),
    )
    db.commit()
    return get_user_by_id(db, cursor.lastrowid)


def get_user_by_email(db: sqlite3.Connection, email: str) -> dict[str, Any] | None:
    """Return a user row by email."""

    row = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return row_to_dict(row)


def get_user_by_id(db: sqlite3.Connection, user_id: int) -> dict[str, Any] | None:
    """Return a user row by id."""

    row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return row_to_dict(row)


def _equipment_for_room(db: sqlite3.Connection, room_id: int) -> list[dict[str, Any]]:
    """Return all equipment linked to a room."""

    rows = db.execute(
        """
        SELECT e.id, e.name, e.description
        FROM equipment e
        JOIN room_equipment re ON re.equipment_id = e.id
        WHERE re.room_id = ?
        ORDER BY e.name
        """,
        (room_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def enrich_room(db: sqlite3.Connection, room: dict[str, Any] | None) -> dict[str, Any] | None:
    """Attach equipment list to a room dictionary."""

    if room is None:
        return None
    room["is_active"] = bool(room["is_active"])
    room["equipment"] = _equipment_for_room(db, room["id"])
    return room


def create_room(db: sqlite3.Connection, room: RoomCreate) -> dict[str, Any]:
    """Create a room."""

    cursor = db.execute(
        """
        INSERT INTO rooms (name, floor, capacity, is_active)
        VALUES (?, ?, ?, ?)
        """,
        (room.name, room.floor, room.capacity, int(room.is_active)),
    )
    db.commit()
    return get_room(db, cursor.lastrowid)


def list_rooms(
    db: sqlite3.Connection,
    min_capacity: int | None = None,
    is_active: bool | None = None,
) -> list[dict[str, Any]]:
    """Return rooms with optional filters."""

    clauses: list[str] = []
    params: list[Any] = []
    if min_capacity is not None:
        clauses.append("capacity >= ?")
        params.append(min_capacity)
    if is_active is not None:
        clauses.append("is_active = ?")
        params.append(int(is_active))
    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = db.execute(f"SELECT * FROM rooms {where_clause} ORDER BY name", params).fetchall()
    return [enrich_room(db, dict(row)) for row in rows]


def get_room(db: sqlite3.Connection, room_id: int) -> dict[str, Any] | None:
    """Return one room by id."""

    row = db.execute("SELECT * FROM rooms WHERE id = ?", (room_id,)).fetchone()
    return enrich_room(db, row_to_dict(row))


def update_room(db: sqlite3.Connection, room_id: int, room: RoomUpdate) -> dict[str, Any] | None:
    """Update room fields."""

    values = room.model_dump(exclude_unset=True)
    if not values:
        return get_room(db, room_id)
    assignments = ", ".join(f"{key} = ?" for key in values)
    params = [int(value) if isinstance(value, bool) else value for value in values.values()]
    params.append(room_id)
    db.execute(f"UPDATE rooms SET {assignments} WHERE id = ?", params)
    db.commit()
    return get_room(db, room_id)


def delete_room(db: sqlite3.Connection, room_id: int) -> bool:
    """Delete a room."""

    cursor = db.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
    db.commit()
    return cursor.rowcount > 0


def create_equipment(db: sqlite3.Connection, item: EquipmentCreate) -> dict[str, Any]:
    """Create an equipment item."""

    cursor = db.execute(
        "INSERT INTO equipment (name, description) VALUES (?, ?)",
        (item.name, item.description),
    )
    db.commit()
    return get_equipment(db, cursor.lastrowid)


def list_equipment(db: sqlite3.Connection) -> list[dict[str, Any]]:
    """Return all equipment items."""

    rows = db.execute("SELECT * FROM equipment ORDER BY name").fetchall()
    return [dict(row) for row in rows]


def get_equipment(db: sqlite3.Connection, equipment_id: int) -> dict[str, Any] | None:
    """Return one equipment item."""

    row = db.execute("SELECT * FROM equipment WHERE id = ?", (equipment_id,)).fetchone()
    return row_to_dict(row)


def update_equipment(
    db: sqlite3.Connection, equipment_id: int, item: EquipmentUpdate
) -> dict[str, Any] | None:
    """Update an equipment item."""

    values = item.model_dump(exclude_unset=True)
    if not values:
        return get_equipment(db, equipment_id)
    assignments = ", ".join(f"{key} = ?" for key in values)
    params = list(values.values()) + [equipment_id]
    db.execute(f"UPDATE equipment SET {assignments} WHERE id = ?", params)
    db.commit()
    return get_equipment(db, equipment_id)


def delete_equipment(db: sqlite3.Connection, equipment_id: int) -> bool:
    """Delete an equipment item."""

    cursor = db.execute("DELETE FROM equipment WHERE id = ?", (equipment_id,))
    db.commit()
    return cursor.rowcount > 0


def add_equipment_to_room(db: sqlite3.Connection, room_id: int, equipment_id: int) -> None:
    """Attach an equipment item to a room."""

    db.execute(
        "INSERT OR IGNORE INTO room_equipment (room_id, equipment_id) VALUES (?, ?)",
        (room_id, equipment_id),
    )
    db.commit()


def remove_equipment_from_room(db: sqlite3.Connection, room_id: int, equipment_id: int) -> bool:
    """Detach an equipment item from a room."""

    cursor = db.execute(
        "DELETE FROM room_equipment WHERE room_id = ? AND equipment_id = ?",
        (room_id, equipment_id),
    )
    db.commit()
    return cursor.rowcount > 0


def has_booking_conflict(
    db: sqlite3.Connection,
    room_id: int,
    start_at: datetime,
    end_at: datetime,
    exclude_booking_id: int | None = None,
) -> bool:
    """Return True when a room has an overlapping active booking."""

    params: list[Any] = [room_id, end_at.isoformat(), start_at.isoformat()]
    clause = ""
    if exclude_booking_id is not None:
        clause = "AND id != ?"
        params.append(exclude_booking_id)
    row = db.execute(
        f"""
        SELECT id FROM bookings
        WHERE room_id = ?
          AND status = 'active'
          AND start_at < ?
          AND end_at > ?
          {clause}
        LIMIT 1
        """,
        params,
    ).fetchone()
    return row is not None


def create_booking(
    db: sqlite3.Connection, booking: BookingCreate, user_id: int
) -> dict[str, Any]:
    """Create a booking."""

    cursor = db.execute(
        """
        INSERT INTO bookings
        (room_id, user_id, title, start_at, end_at, participants_count)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            booking.room_id,
            user_id,
            booking.title,
            booking.start_at.isoformat(),
            booking.end_at.isoformat(),
            booking.participants_count,
        ),
    )
    db.commit()
    return get_booking(db, cursor.lastrowid)


def list_bookings(
    db: sqlite3.Connection,
    user_id: int | None = None,
    room_id: int | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """Return bookings with optional filters."""

    clauses: list[str] = []
    params: list[Any] = []
    if user_id is not None:
        clauses.append("user_id = ?")
        params.append(user_id)
    if room_id is not None:
        clauses.append("room_id = ?")
        params.append(room_id)
    if status is not None:
        clauses.append("status = ?")
        params.append(status)
    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = db.execute(
        f"SELECT * FROM bookings {where_clause} ORDER BY start_at DESC", params
    ).fetchall()
    return [dict(row) for row in rows]


def get_booking(db: sqlite3.Connection, booking_id: int) -> dict[str, Any] | None:
    """Return one booking."""

    row = db.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    return row_to_dict(row)


def update_booking(
    db: sqlite3.Connection, booking_id: int, booking: BookingUpdate
) -> dict[str, Any] | None:
    """Update a booking."""

    values = booking.model_dump(exclude_unset=True)
    if not values:
        return get_booking(db, booking_id)
    for key in ("start_at", "end_at"):
        if values.get(key) is not None:
            values[key] = values[key].isoformat()
    if "status" in values and values["status"] is not None:
        values["status"] = values["status"].value
    assignments = ", ".join(f"{key} = ?" for key in values)
    params = list(values.values()) + [booking_id]
    db.execute(f"UPDATE bookings SET {assignments} WHERE id = ?", params)
    db.commit()
    return get_booking(db, booking_id)


def delete_booking(db: sqlite3.Connection, booking_id: int) -> bool:
    """Delete a booking."""

    cursor = db.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    db.commit()
    return cursor.rowcount > 0


def room_has_equipment(
    db: sqlite3.Connection, room_id: int, required_equipment_ids: list[int]
) -> bool:
    """Return True when the room contains all required equipment items."""

    if not required_equipment_ids:
        return True
    placeholders = ",".join("?" for _ in required_equipment_ids)
    rows = db.execute(
        f"""
        SELECT equipment_id FROM room_equipment
        WHERE room_id = ? AND equipment_id IN ({placeholders})
        """,
        [room_id, *required_equipment_ids],
    ).fetchall()
    return {row["equipment_id"] for row in rows} == set(required_equipment_ids)
