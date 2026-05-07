from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Booking, BookingStatus, Venue, ContentCreator
from app.schemas import BookingCreate, BookingOut, BookingUpdate

router = APIRouter(prefix="/bookings", tags=["bookings"])


def _check_conflict(db: Session, venue_id: int, start_time, end_time, exclude_id: Optional[int] = None):
    q = (
        db.query(Booking)
        .filter(
            Booking.venue_id == venue_id,
            Booking.status != BookingStatus.cancelled,
            Booking.start_time < end_time,
            Booking.end_time > start_time,
        )
    )
    if exclude_id:
        q = q.filter(Booking.id != exclude_id)
    return q.first()


@router.post("/", response_model=BookingOut, status_code=201)
def create_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    if not db.get(Venue, booking.venue_id):
        raise HTTPException(status_code=404, detail="Venue not found")
    if not db.get(ContentCreator, booking.creator_id):
        raise HTTPException(status_code=404, detail="Creator not found")
    if _check_conflict(db, booking.venue_id, booking.start_time, booking.end_time):
        raise HTTPException(status_code=409, detail="Venue is already booked for this time slot")
    db_booking = Booking(**booking.model_dump())
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db.query(Booking).options(joinedload(Booking.venue), joinedload(Booking.creator)).get(db_booking.id)


@router.get("/", response_model=List[BookingOut])
def list_bookings(
    venue_id: Optional[int] = Query(None),
    creator_id: Optional[int] = Query(None),
    status: Optional[BookingStatus] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Booking).options(joinedload(Booking.venue), joinedload(Booking.creator))
    if venue_id:
        q = q.filter(Booking.venue_id == venue_id)
    if creator_id:
        q = q.filter(Booking.creator_id == creator_id)
    if status:
        q = q.filter(Booking.status == status)
    return q.all()


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = (
        db.query(Booking)
        .options(joinedload(Booking.venue), joinedload(Booking.creator))
        .filter(Booking.id == booking_id)
        .first()
    )
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.patch("/{booking_id}", response_model=BookingOut)
def update_booking(booking_id: int, updates: BookingUpdate, db: Session = Depends(get_db)):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    new_start = updates.start_time or booking.start_time
    new_end = updates.end_time or booking.end_time

    if updates.start_time or updates.end_time:
        if new_end <= new_start:
            raise HTTPException(status_code=400, detail="end_time must be after start_time")
        if _check_conflict(db, booking.venue_id, new_start, new_end, exclude_id=booking_id):
            raise HTTPException(status_code=409, detail="Venue is already booked for this time slot")

    for field, value in updates.model_dump(exclude_none=True).items():
        setattr(booking, field, value)
    db.commit()
    db.refresh(booking)
    return (
        db.query(Booking)
        .options(joinedload(Booking.venue), joinedload(Booking.creator))
        .filter(Booking.id == booking_id)
        .first()
    )


@router.delete("/{booking_id}", status_code=204)
def delete_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    db.delete(booking)
    db.commit()
