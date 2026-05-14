"""Business algorithm for recommending rooms and meeting time slots."""

from datetime import datetime, timedelta
import sqlite3

from app.schemas import SlotRecommendation, SlotRecommendationRequest
from app.services import crud


def _active_overlapping_bookings(
    db: sqlite3.Connection, room_id: int, start_at: datetime, end_at: datetime
) -> list[dict]:
    """Return active bookings that overlap the requested search window."""

    rows = db.execute(
        """
        SELECT * FROM bookings
        WHERE room_id = ?
          AND status = 'active'
          AND start_at < ?
          AND end_at > ?
        ORDER BY start_at
        """,
        (room_id, end_at.isoformat(), start_at.isoformat()),
    ).fetchall()
    return [dict(row) for row in rows]


def _candidate_start(
    free_start: datetime,
    free_end: datetime,
    duration: timedelta,
    preferred_start: datetime | None,
) -> datetime | None:
    """Choose a candidate start inside a free interval."""

    if preferred_start and free_start <= preferred_start and preferred_start + duration <= free_end:
        return preferred_start
    if free_start + duration <= free_end:
        return free_start
    return None


def _score_candidate(
    room: dict,
    request: SlotRecommendationRequest,
    start_at: datetime,
) -> tuple[float, str]:
    """Calculate an explainable slot score: lower is better."""

    spare_capacity = room["capacity"] - request.participants_count
    capacity_penalty = spare_capacity * 1.5
    preferred_penalty = 0.0
    if request.preferred_start is not None:
        preferred_penalty = abs((start_at - request.preferred_start).total_seconds()) / 60
    equipment_count = len(room.get("equipment", []))
    equipment_penalty = max(0, equipment_count - len(request.required_equipment_ids)) * 0.25
    score = capacity_penalty + preferred_penalty + equipment_penalty
    reason = (
        f"Свободный слот найден; запас мест: {spare_capacity}; "
        f"отклонение от предпочтительного времени: {preferred_penalty:.0f} мин.; "
        f"итоговый score: {score:.2f}"
    )
    return round(score, 2), reason


def recommend_slots(
    db: sqlite3.Connection, request: SlotRecommendationRequest, limit: int = 3
) -> list[SlotRecommendation]:
    """Return the best available room/time recommendations."""

    duration = timedelta(minutes=request.duration_minutes)
    rooms = crud.list_rooms(db, min_capacity=request.participants_count, is_active=True)
    recommendations: list[SlotRecommendation] = []

    for room in rooms:
        if not crud.room_has_equipment(db, room["id"], request.required_equipment_ids):
            continue
        cursor = request.window_start
        bookings = _active_overlapping_bookings(
            db, room["id"], request.window_start, request.window_end
        )
        for booking in bookings:
            busy_start = datetime.fromisoformat(booking["start_at"])
            busy_end = datetime.fromisoformat(booking["end_at"])
            free_start = max(cursor, request.window_start)
            free_end = min(busy_start, request.window_end)
            start_at = _candidate_start(free_start, free_end, duration, request.preferred_start)
            if start_at is not None:
                score, reason = _score_candidate(room, request, start_at)
                recommendations.append(
                    SlotRecommendation(
                        room_id=room["id"],
                        room_name=room["name"],
                        start_at=start_at,
                        end_at=start_at + duration,
                        score=score,
                        score_reason=reason,
                    )
                )
            cursor = max(cursor, busy_end)
        start_at = _candidate_start(cursor, request.window_end, duration, request.preferred_start)
        if start_at is not None:
            score, reason = _score_candidate(room, request, start_at)
            recommendations.append(
                SlotRecommendation(
                    room_id=room["id"],
                    room_name=room["name"],
                    start_at=start_at,
                    end_at=start_at + duration,
                    score=score,
                    score_reason=reason,
                )
            )

    recommendations.sort(key=lambda item: (item.score, item.start_at, item.room_id))
    return recommendations[:limit]
