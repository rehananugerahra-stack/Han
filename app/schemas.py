from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator

from app.models import VenueType, BookingStatus


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
