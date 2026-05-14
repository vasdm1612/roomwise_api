"""Administrative analytical report routes."""

from datetime import datetime
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.schemas import RoomUtilizationReport
from app.services.reports import build_room_utilization_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/room-utilization", response_model=RoomUtilizationReport)
def room_utilization_report(
    period_start: datetime = Query(..., description="Report period start"),
    period_end: datetime = Query(..., description="Report period end"),
    db: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
) -> dict:
    """Return room utilization statistics for the selected period."""

    if period_start >= period_end:
        raise HTTPException(status_code=422, detail="period_start must be earlier than period_end")
    return build_room_utilization_report(db, period_start, period_end)
