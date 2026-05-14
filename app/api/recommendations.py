"""Recommendation endpoint."""

import sqlite3

from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas import SlotRecommendation, SlotRecommendationRequest
from app.services.recommendations import recommend_slots

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/slots", response_model=list[SlotRecommendation])
def recommend_meeting_slots(
    request: SlotRecommendationRequest,
    db: sqlite3.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> list[SlotRecommendation]:
    """Return the top available room/time slots for a meeting."""

    return recommend_slots(db, request)
