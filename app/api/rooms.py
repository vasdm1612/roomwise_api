"""Room CRUD routes and room-equipment linking routes."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.schemas import RoomCreate, RoomRead, RoomUpdate
from app.services import crud

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("", response_model=RoomRead, status_code=status.HTTP_201_CREATED)
def create_room(
    room: RoomCreate,
    db: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
) -> dict:
    """Create a room."""

    try:
        return crud.create_room(db, room)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Room already exists") from exc


@router.get("", response_model=list[RoomRead])
def list_rooms(
    min_capacity: int | None = Query(default=None, gt=0),
    is_active: bool | None = None,
    db: sqlite3.Connection = Depends(get_db),
) -> list[dict]:
    """List rooms with optional filters."""

    return crud.list_rooms(db, min_capacity=min_capacity, is_active=is_active)


@router.get("/{room_id}", response_model=RoomRead)
def get_room(room_id: int, db: sqlite3.Connection = Depends(get_db)) -> dict:
    """Return one room."""

    room = crud.get_room(db, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.patch("/{room_id}", response_model=RoomRead)
def update_room(
    room_id: int,
    room: RoomUpdate,
    db: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
) -> dict:
    """Update a room."""

    if crud.get_room(db, room_id) is None:
        raise HTTPException(status_code=404, detail="Room not found")
    try:
        return crud.update_room(db, room_id, room)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Room already exists") from exc


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(
    room_id: int,
    db: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
) -> None:
    """Delete a room."""

    if not crud.delete_room(db, room_id):
        raise HTTPException(status_code=404, detail="Room not found")


@router.post("/{room_id}/equipment/{equipment_id}", response_model=RoomRead)
def attach_equipment(
    room_id: int,
    equipment_id: int,
    db: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
) -> dict:
    """Attach equipment to a room."""

    if crud.get_room(db, room_id) is None:
        raise HTTPException(status_code=404, detail="Room not found")
    if crud.get_equipment(db, equipment_id) is None:
        raise HTTPException(status_code=404, detail="Equipment not found")
    crud.add_equipment_to_room(db, room_id, equipment_id)
    return crud.get_room(db, room_id)


@router.delete("/{room_id}/equipment/{equipment_id}", response_model=RoomRead)
def detach_equipment(
    room_id: int,
    equipment_id: int,
    db: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
) -> dict:
    """Detach equipment from a room."""

    if crud.get_room(db, room_id) is None:
        raise HTTPException(status_code=404, detail="Room not found")
    if crud.get_equipment(db, equipment_id) is None:
        raise HTTPException(status_code=404, detail="Equipment not found")
    if not crud.remove_equipment_from_room(db, room_id, equipment_id):
        raise HTTPException(status_code=404, detail="Room-equipment link not found")
    return crud.get_room(db, room_id)
