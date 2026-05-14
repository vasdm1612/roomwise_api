"""Application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from app.api import auth, bookings, equipment, recommendations, reports, rooms
from app.core.database import init_db


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize the SQLite database on application startup."""

    init_db()
    yield


app = FastAPI(
    title="RoomWise API",
    description="REST-сервис бронирования переговорных комнат и рекомендации слотов.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(rooms.router)
app.include_router(equipment.router)
app.include_router(bookings.router)
app.include_router(recommendations.router)
app.include_router(reports.router)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Return service health status."""

    return {"status": "ok"}
