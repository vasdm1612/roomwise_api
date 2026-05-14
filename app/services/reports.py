"""Analytical services for administrative reports."""

from datetime import datetime
import sqlite3
from typing import Any


def _overlap_minutes(
    start_at: datetime,
    end_at: datetime,
    period_start: datetime,
    period_end: datetime,
) -> int:
    """Return overlap duration in full minutes."""

    overlap_start = max(start_at, period_start)
    overlap_end = min(end_at, period_end)
    if overlap_start >= overlap_end:
        return 0
    return int((overlap_end - overlap_start).total_seconds() // 60)


def build_room_utilization_report(
    db: sqlite3.Connection,
    period_start: datetime,
    period_end: datetime,
) -> dict[str, Any]:
    """Calculate room utilization statistics for an admin dashboard."""

    period_minutes = int((period_end - period_start).total_seconds() // 60)
    room_rows = db.execute("SELECT * FROM rooms ORDER BY name").fetchall()
    rooms: list[dict[str, Any]] = []

    for room_row in room_rows:
        room = dict(room_row)
        booking_rows = db.execute(
            """
            SELECT start_at, end_at
            FROM bookings
            WHERE room_id = ?
              AND status = 'active'
              AND start_at < ?
              AND end_at > ?
            """,
            (room["id"], period_end.isoformat(), period_start.isoformat()),
        ).fetchall()
        booked_minutes = sum(
            _overlap_minutes(
                datetime.fromisoformat(row["start_at"]),
                datetime.fromisoformat(row["end_at"]),
                period_start,
                period_end,
            )
            for row in booking_rows
        )
        utilization_percent = 0.0
        if period_minutes > 0:
            utilization_percent = round(booked_minutes / period_minutes * 100, 2)
        rooms.append(
            {
                "room_id": room["id"],
                "room_name": room["name"],
                "booked_minutes": booked_minutes,
                "available_minutes": max(period_minutes - booked_minutes, 0),
                "utilization_percent": utilization_percent,
            }
        )

    rooms.sort(key=lambda item: (-item["utilization_percent"], item["room_name"]))
    return {
        "period_start": period_start,
        "period_end": period_end,
        "rooms": rooms,
    }
