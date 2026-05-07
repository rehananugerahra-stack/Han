from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class VenueType(str, enum.Enum):
    studio = "studio"
    outdoor = "outdoor"
    indoor = "indoor"
    rooftop = "rooftop"
    warehouse = "warehouse"


class BookingStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"


class Venue(Base):
    __tablename__ = "venues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    location = Column(String, nullable=False)
    venue_type = Column(SAEnum(VenueType), nullable=False)
    capacity = Column(Integer, nullable=False)
    hourly_rate = Column(Float, nullable=False)
    amenities = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    bookings = relationship("Booking", back_populates="venue")


class ContentCreator(Base):
    __tablename__ = "content_creators"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    niche = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    bookings = relationship("Booking", back_populates="creator")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False)
    creator_id = Column(Integer, ForeignKey("content_creators.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(SAEnum(BookingStatus), default=BookingStatus.pending)
    notes = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    venue = relationship("Venue", back_populates="bookings")
    creator = relationship("ContentCreator", back_populates="bookings")
