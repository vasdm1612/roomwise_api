"""Booking CRUD routes."""

from datetime import datetime
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas import BookingCreate, BookingRead, BookingStatus, BookingUpdate
from app.services import crud

router = APIRouter(prefix="/bookings", tags=["bookings"])


def _ensure_booking_allowed(booking: dict | None, current_user: dict) -> dict:
    """Check that a booking exists and belongs to the current user or admin."""

    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    if current_user["role"] != "admin" and booking["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access to this booking is forbidden")
    return booking


def _validate_booking_business_rules(
    db: sqlite3.Connection,
    room_id: int,
    participants_count: int,
    start_at: datetime,
    end_at: datetime,
    exclude_booking_id: int | None = None,
) -> None:
    """Validate capacity, room state and time conflicts."""

    room = crud.get_room(db, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    if not room["is_active"]:
        raise HTTPException(status_code=409, detail="Room is inactive")
    if participants_count > room["capacity"]:
        raise HTTPException(status_code=409, detail="Room capacity is too small")
    if crud.has_booking_conflict(db, room_id, start_at, end_at, exclude_booking_id):
        raise HTTPException(status_code=409, detail="Booking overlaps with an existing booking")


@router.post("", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking: BookingCreate,
    db: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Create a booking for the current user."""

    _validate_booking_business_rules(
        db, booking.room_id, booking.participants_count, booking.start_at, booking.end_at
    )
    return crud.create_booking(db, booking, current_user["id"])


@router.get("", response_model=list[BookingRead])
def list_bookings(
    room_id: int | None = Query(default=None, gt=0),
    status_filter: BookingStatus | None = Query(default=None, alias="status"),
    db: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """List own bookings; admins can see every booking."""

    user_filter = None if current_user["role"] == "admin" else current_user["id"]
    status_value = status_filter.value if status_filter else None
    return crud.list_bookings(db, user_id=user_filter, room_id=room_id, status=status_value)


@router.get("/{booking_id}", response_model=BookingRead)
def get_booking(
    booking_id: int,
    db: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Return one booking."""

    return _ensure_booking_allowed(crud.get_booking(db, booking_id), current_user)


@router.patch("/{booking_id}", response_model=BookingRead)
def update_booking(
    booking_id: int,
    patch: BookingUpdate,
    db: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Update a booking."""

    existing = _ensure_booking_allowed(crud.get_booking(db, booking_id), current_user)
    start_at = patch.start_at or datetime.fromisoformat(existing["start_at"])
    end_at = patch.end_at or datetime.fromisoformat(existing["end_at"])
    participants = patch.participants_count or existing["participants_count"]
    if patch.status != BookingStatus.CANCELLED:
        _validate_booking_business_rules(
            db,
            existing["room_id"],
            participants,
            start_at,
            end_at,
            exclude_booking_id=booking_id,
        )
    return crud.update_booking(db, booking_id, patch)


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(
    booking_id: int,
    db: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> None:
    """Delete a booking."""

    _ensure_booking_allowed(crud.get_booking(db, booking_id), current_user)
    crud.delete_booking(db, booking_id)
