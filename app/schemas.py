"""Pydantic schemas for request validation and API responses."""

from datetime import datetime, timedelta
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class UserRole(StrEnum):
    """Supported user roles."""

    USER = "user"
    ADMIN = "admin"


class BookingStatus(StrEnum):
    """Supported booking statuses."""

    ACTIVE = "active"
    CANCELLED = "cancelled"


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class UserBase(BaseModel):
    """Common user fields."""

    email: EmailStr
    full_name: Annotated[str, Field(min_length=2, max_length=120)]


class UserCreate(UserBase):
    """User registration payload."""

    password: Annotated[str, Field(min_length=8, max_length=128)]
    role: UserRole = UserRole.USER


class UserLogin(BaseModel):
    """User login payload."""

    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=128)]


class UserRead(UserBase):
    """Public user representation."""

    id: int
    role: UserRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class RoomBase(BaseModel):
    """Common room fields."""

    name: Annotated[str, Field(min_length=2, max_length=80)]
    floor: Annotated[int, Field(ge=-5, le=150)]
    capacity: Annotated[int, Field(gt=0, le=500)]
    is_active: bool = True


class RoomCreate(RoomBase):
    """Room creation payload."""


class RoomUpdate(BaseModel):
    """Room update payload."""

    name: Annotated[str | None, Field(default=None, min_length=2, max_length=80)]
    floor: Annotated[int | None, Field(default=None, ge=-5, le=150)]
    capacity: Annotated[int | None, Field(default=None, gt=0, le=500)]
    is_active: bool | None = None


class EquipmentRead(BaseModel):
    """Equipment response."""

    id: int
    name: str
    description: str


class RoomRead(RoomBase):
    """Room response with equipment list."""

    id: int
    equipment: list[EquipmentRead] = Field(default_factory=list)


class EquipmentCreate(BaseModel):
    """Equipment creation payload."""

    name: Annotated[str, Field(min_length=2, max_length=80)]
    description: Annotated[str, Field(default="", max_length=300)] = ""


class EquipmentUpdate(BaseModel):
    """Equipment update payload."""

    name: Annotated[str | None, Field(default=None, min_length=2, max_length=80)]
    description: Annotated[str | None, Field(default=None, max_length=300)]


class BookingBase(BaseModel):
    """Common booking fields."""

    room_id: int
    title: Annotated[str, Field(min_length=2, max_length=120)]
    start_at: datetime
    end_at: datetime
    participants_count: Annotated[int, Field(gt=0, le=500)]

    @model_validator(mode="after")
    def validate_dates(self) -> "BookingBase":
        """Ensure a booking has a positive duration."""

        if self.start_at >= self.end_at:
            raise ValueError("start_at must be earlier than end_at")
        return self


class BookingCreate(BookingBase):
    """Booking creation payload."""


class BookingUpdate(BaseModel):
    """Booking update payload."""

    title: Annotated[str | None, Field(default=None, min_length=2, max_length=120)]
    start_at: datetime | None = None
    end_at: datetime | None = None
    participants_count: Annotated[int | None, Field(default=None, gt=0, le=500)]
    status: BookingStatus | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "BookingUpdate":
        """Validate date order when both dates are supplied."""

        if self.start_at and self.end_at and self.start_at >= self.end_at:
            raise ValueError("start_at must be earlier than end_at")
        return self


class BookingRead(BookingBase):
    """Booking response."""

    id: int
    user_id: int
    status: BookingStatus


class SlotRecommendationRequest(BaseModel):
    """Payload for the room and slot recommendation algorithm."""

    window_start: datetime
    window_end: datetime
    duration_minutes: Annotated[int, Field(ge=15, le=480)]
    participants_count: Annotated[int, Field(gt=0, le=500)]
    required_equipment_ids: list[int] = Field(default_factory=list)
    preferred_start: datetime | None = None

    @field_validator("required_equipment_ids")
    @classmethod
    def validate_unique_equipment(cls, values: list[int]) -> list[int]:
        """Require unique positive equipment ids."""

        if any(value <= 0 for value in values):
            raise ValueError("equipment ids must be positive")
        if len(values) != len(set(values)):
            raise ValueError("equipment ids must be unique")
        return values

    @model_validator(mode="after")
    def validate_window(self) -> "SlotRecommendationRequest":
        """Validate requested search window and preferred start."""

        if self.window_start >= self.window_end:
            raise ValueError("window_start must be earlier than window_end")
        if self.window_start + timedelta(minutes=self.duration_minutes) > self.window_end:
            raise ValueError("duration does not fit into the selected window")
        if self.preferred_start and not (
            self.window_start <= self.preferred_start <= self.window_end
        ):
            raise ValueError("preferred_start must be inside the selected window")
        return self


class SlotRecommendation(BaseModel):
    """Recommended room and time slot."""

    room_id: int
    room_name: str
    start_at: datetime
    end_at: datetime
    score: float
    score_reason: str


class RoomUtilizationItem(BaseModel):
    """Room utilization metric for a selected period."""

    room_id: int
    room_name: str
    booked_minutes: int
    available_minutes: int
    utilization_percent: float


class RoomUtilizationReport(BaseModel):
    """Administrative report with room utilization statistics."""

    period_start: datetime
    period_end: datetime
    rooms: list[RoomUtilizationItem]


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
