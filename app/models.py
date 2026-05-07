from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SAEnum, Boolean
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


class EventType(str, enum.Enum):
    live_music = "live_music"
    food_festival = "food_festival"
    themed_night = "themed_night"
    pop_up_market = "pop_up_market"
    happy_hour = "happy_hour"
    trivia_night = "trivia_night"
    cooking_class = "cooking_class"
    influencer_collab = "influencer_collab"


class EventStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    cancelled = "cancelled"
    completed = "completed"


class PromoType(str, enum.Enum):
    happy_hour = "happy_hour"
    bundle_deal = "bundle_deal"
    early_bird = "early_bird"
    loyalty_discount = "loyalty_discount"
    influencer_code = "influencer_code"
    flash_sale = "flash_sale"


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
    events = relationship("EventDay", back_populates="venue")
    promotions = relationship("Promotion", back_populates="venue")


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


class EventDay(Base):
    __tablename__ = "event_days"

    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, default="")
    event_type = Column(SAEnum(EventType), nullable=False)
    status = Column(SAEnum(EventStatus), default=EventStatus.draft)
    event_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    ticket_price = Column(Float, default=0.0)
    expected_attendance = Column(Integer, default=0)
    actual_attendance = Column(Integer, nullable=True)
    revenue_goal = Column(Float, default=0.0)
    actual_revenue = Column(Float, nullable=True)
    target_audience = Column(String, default="")
    # why this event drives restaurant foot traffic and sales
    business_rationale = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    venue = relationship("Venue", back_populates="events")


class Promotion(Base):
    __tablename__ = "promotions"

    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    promo_type = Column(SAEnum(PromoType), nullable=False)
    code = Column(String, unique=True, nullable=False, index=True)
    discount_percent = Column(Float, nullable=True)
    discount_amount = Column(Float, nullable=True)
    min_spend = Column(Float, default=0.0)
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    max_usage = Column(Integer, nullable=True)
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    venue = relationship("Venue", back_populates="promotions")
