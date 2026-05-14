"""Equipment CRUD routes."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.schemas import EquipmentCreate, EquipmentRead, EquipmentUpdate
from app.services import crud

router = APIRouter(prefix="/equipment", tags=["equipment"])


@router.post("", response_model=EquipmentRead, status_code=status.HTTP_201_CREATED)
def create_item(
    item: EquipmentCreate,
    db: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
) -> dict:
    """Create an equipment item."""

    try:
        return crud.create_equipment(db, item)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Equipment already exists") from exc


@router.get("", response_model=list[EquipmentRead])
def list_items(db: sqlite3.Connection = Depends(get_db)) -> list[dict]:
    """List equipment items."""

    return crud.list_equipment(db)


@router.patch("/{equipment_id}", response_model=EquipmentRead)
def update_item(
    equipment_id: int,
    item: EquipmentUpdate,
    db: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
) -> dict:
    """Update an equipment item."""

    if crud.get_equipment(db, equipment_id) is None:
        raise HTTPException(status_code=404, detail="Equipment not found")
    try:
        return crud.update_equipment(db, equipment_id, item)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Equipment already exists") from exc


@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    equipment_id: int,
    db: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
) -> None:
    """Delete an equipment item."""

    if not crud.delete_equipment(db, equipment_id):
        raise HTTPException(status_code=404, detail="Equipment not found")
