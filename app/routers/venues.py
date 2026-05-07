from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Venue, VenueType
from app.schemas import VenueCreate, VenueOut, VenueUpdate

router = APIRouter(prefix="/venues", tags=["venues"])


@router.post("/", response_model=VenueOut, status_code=201)
def create_venue(venue: VenueCreate, db: Session = Depends(get_db)):
    db_venue = Venue(**venue.model_dump())
    db.add(db_venue)
    db.commit()
    db.refresh(db_venue)
    return db_venue


@router.get("/", response_model=List[VenueOut])
def list_venues(
    venue_type: Optional[VenueType] = Query(None),
    min_capacity: Optional[int] = Query(None),
    max_rate: Optional[float] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Venue)
    if venue_type:
        q = q.filter(Venue.venue_type == venue_type)
    if min_capacity is not None:
        q = q.filter(Venue.capacity >= min_capacity)
    if max_rate is not None:
        q = q.filter(Venue.hourly_rate <= max_rate)
    return q.all()


@router.get("/{venue_id}", response_model=VenueOut)
def get_venue(venue_id: int, db: Session = Depends(get_db)):
    venue = db.get(Venue, venue_id)
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    return venue


@router.patch("/{venue_id}", response_model=VenueOut)
def update_venue(venue_id: int, updates: VenueUpdate, db: Session = Depends(get_db)):
    venue = db.get(Venue, venue_id)
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    for field, value in updates.model_dump(exclude_none=True).items():
        setattr(venue, field, value)
    db.commit()
    db.refresh(venue)
    return venue


@router.delete("/{venue_id}", status_code=204)
def delete_venue(venue_id: int, db: Session = Depends(get_db)):
    venue = db.get(Venue, venue_id)
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    db.delete(venue)
    db.commit()
