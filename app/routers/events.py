from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import EventDay, EventStatus, EventType, Venue
from app.schemas import EventDayCreate, EventDayOut, EventDayUpdate

router = APIRouter(prefix="/events", tags=["events"])

# Business rationale templates surfaced when no custom rationale is provided
_RATIONALE = {
    EventType.live_music: (
        "Live music draws walk-in crowds who stay longer and spend 30-40% more per head. "
        "Nearby restaurants benefit from pre/post-show dining surges and social media exposure "
        "from attendees tagging their location."
    ),
    EventType.food_festival: (
        "Food festivals create a destination effect — visitors actively seek out surrounding "
        "eateries to compare flavors, directly driving incremental covers and average spend."
    ),
    EventType.themed_night: (
        "Themed nights generate shareable moments, fueling organic UGC that reaches audiences "
        "10x the venue capacity. Restaurants nearby capture the overflow and the social impressions."
    ),
    EventType.pop_up_market: (
        "Pop-up markets extend dwell time in the area by 45-90 minutes, converting browsers "
        "into diners. Complementary food & beverage spend rises as shoppers pause between stalls."
    ),
    EventType.happy_hour: (
        "Happy hour anchors the 4–7 pm dead zone, the weakest revenue window for most restaurants. "
        "Synchronising promotions with nearby venues creates a corridor effect and cross-referral."
    ),
    EventType.trivia_night: (
        "Weekly trivia builds habitual visitation — teams return every week, guaranteeing "
        "predictable mid-week revenue and reducing reliance on weekend peaks."
    ),
    EventType.cooking_class: (
        "Cooking classes position the restaurant as a culinary authority, commanding premium "
        "pricing, driving merchandise sales, and converting class attendees into loyal regulars."
    ),
    EventType.influencer_collab: (
        "A single micro-influencer post (10k–100k followers) yields an average 3–5x return on "
        "collaboration cost through direct reservation spikes in the 48 hours after posting."
    ),
}


@router.post("/", response_model=EventDayOut, status_code=201)
def create_event(event: EventDayCreate, db: Session = Depends(get_db)):
    if not db.get(Venue, event.venue_id):
        raise HTTPException(status_code=404, detail="Venue not found")
    data = event.model_dump()
    if not data.get("business_rationale"):
        data["business_rationale"] = _RATIONALE.get(data["event_type"], "")
    db_event = EventDay(**data)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return _load(db, db_event.id)


@router.get("/", response_model=List[EventDayOut])
def list_events(
    venue_id: Optional[int] = Query(None),
    event_type: Optional[EventType] = Query(None),
    status: Optional[EventStatus] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(EventDay).options(joinedload(EventDay.venue))
    if venue_id:
        q = q.filter(EventDay.venue_id == venue_id)
    if event_type:
        q = q.filter(EventDay.event_type == event_type)
    if status:
        q = q.filter(EventDay.status == status)
    return q.order_by(EventDay.event_date).all()


@router.get("/{event_id}", response_model=EventDayOut)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = _load(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.patch("/{event_id}", response_model=EventDayOut)
def update_event(event_id: int, updates: EventDayUpdate, db: Session = Depends(get_db)):
    event = db.get(EventDay, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    for field, value in updates.model_dump(exclude_none=True).items():
        setattr(event, field, value)
    db.commit()
    return _load(db, event_id)


@router.delete("/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.get(EventDay, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(event)
    db.commit()


def _load(db: Session, event_id: int):
    return (
        db.query(EventDay)
        .options(joinedload(EventDay.venue))
        .filter(EventDay.id == event_id)
        .first()
    )
