from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator

from app.models import VenueType, BookingStatus, EventType, EventStatus, PromoType


class VenueBase(BaseModel):
    name: str
    location: str
    venue_type: VenueType
    capacity: int
    hourly_rate: float
    amenities: Optional[str] = ""


class VenueCreate(VenueBase):
    @field_validator("capacity")
    @classmethod
    def capacity_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("capacity must be positive")
        return v

    @field_validator("hourly_rate")
    @classmethod
    def rate_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("hourly_rate must be positive")
        return v


class VenueUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    venue_type: Optional[VenueType] = None
    capacity: Optional[int] = None
    hourly_rate: Optional[float] = None
    amenities: Optional[str] = None


class VenueOut(VenueBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CreatorBase(BaseModel):
    name: str
    email: EmailStr
    niche: str
    platform: str


class CreatorCreate(CreatorBase):
    pass


class CreatorUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    niche: Optional[str] = None
    platform: Optional[str] = None


class CreatorOut(CreatorBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class BookingBase(BaseModel):
    venue_id: int
    creator_id: int
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = ""


class BookingCreate(BookingBase):
    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, v: datetime, info) -> datetime:
        start = info.data.get("start_time")
        if start and v <= start:
            raise ValueError("end_time must be after start_time")
        return v


class BookingUpdate(BaseModel):
    status: Optional[BookingStatus] = None
    notes: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class BookingOut(BookingBase):
    id: int
    status: BookingStatus
    created_at: datetime
    venue: VenueOut
    creator: CreatorOut

    model_config = {"from_attributes": True}


# ── Event Day ─────────────────────────────────────────────────────────────────

class EventDayBase(BaseModel):
    venue_id: int
    title: str
    description: Optional[str] = ""
    event_type: EventType
    event_date: datetime
    end_date: datetime
    ticket_price: Optional[float] = 0.0
    expected_attendance: Optional[int] = 0
    revenue_goal: Optional[float] = 0.0
    target_audience: Optional[str] = ""
    business_rationale: Optional[str] = ""


class EventDayCreate(EventDayBase):
    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v: datetime, info) -> datetime:
        start = info.data.get("event_date")
        if start and v <= start:
            raise ValueError("end_date must be after event_date")
        return v

    @field_validator("ticket_price")
    @classmethod
    def price_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("ticket_price cannot be negative")
        return v


class EventDayUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[EventType] = None
    status: Optional[EventStatus] = None
    event_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    ticket_price: Optional[float] = None
    expected_attendance: Optional[int] = None
    actual_attendance: Optional[int] = None
    revenue_goal: Optional[float] = None
    actual_revenue: Optional[float] = None
    target_audience: Optional[str] = None
    business_rationale: Optional[str] = None


class EventDayOut(EventDayBase):
    id: int
    status: EventStatus
    actual_attendance: Optional[int] = None
    actual_revenue: Optional[float] = None
    created_at: datetime
    venue: VenueOut

    model_config = {"from_attributes": True}


# ── Promotion ─────────────────────────────────────────────────────────────────

class PromotionBase(BaseModel):
    venue_id: Optional[int] = None
    name: str
    description: Optional[str] = ""
    promo_type: PromoType
    code: str
    discount_percent: Optional[float] = None
    discount_amount: Optional[float] = None
    min_spend: Optional[float] = 0.0
    valid_from: datetime
    valid_until: datetime
    max_usage: Optional[int] = None


class PromotionCreate(PromotionBase):
    @field_validator("valid_until")
    @classmethod
    def until_after_from(cls, v: datetime, info) -> datetime:
        vf = info.data.get("valid_from")
        if vf and v <= vf:
            raise ValueError("valid_until must be after valid_from")
        return v

    @field_validator("discount_percent")
    @classmethod
    def pct_range(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0 < v <= 100):
            raise ValueError("discount_percent must be between 0 and 100")
        return v


class PromotionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    valid_until: Optional[datetime] = None
    max_usage: Optional[int] = None
    discount_percent: Optional[float] = None
    discount_amount: Optional[float] = None


class PromotionOut(PromotionBase):
    id: int
    usage_count: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
