from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Competitor, CompetitorMenuItem, CompetitorType, MenuCategory
from app.schemas import (
    CompetitorCreate, CompetitorOut, CompetitorUpdate,
    CompetitorMenuItemCreate, CompetitorMenuItemOut, CompetitorMenuItemUpdate,
)

router = APIRouter(prefix="/competitors", tags=["competitor pricing"])


# ── Competitors ───────────────────────────────────────────────────────────────

@router.post("/", response_model=CompetitorOut, status_code=201)
def add_competitor(data: CompetitorCreate, db: Session = Depends(get_db)):
    competitor = Competitor(**data.model_dump())
    db.add(competitor)
    db.commit()
    db.refresh(competitor)
    return _load(db, competitor.id)


@router.get("/", response_model=List[CompetitorOut])
def list_competitors(
    competitor_type: Optional[CompetitorType] = Query(None),
    max_distance: Optional[int] = Query(None, description="Max distance in metres"),
    db: Session = Depends(get_db),
):
    q = db.query(Competitor).options(joinedload(Competitor.menu_items))
    if competitor_type:
        q = q.filter(Competitor.competitor_type == competitor_type)
    if max_distance is not None:
        q = q.filter(Competitor.distance_meters <= max_distance)
    return q.order_by(Competitor.distance_meters).all()


@router.get("/{competitor_id}", response_model=CompetitorOut)
def get_competitor(competitor_id: int, db: Session = Depends(get_db)):
    c = _load(db, competitor_id)
    if not c:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return c


@router.patch("/{competitor_id}", response_model=CompetitorOut)
def update_competitor(competitor_id: int, updates: CompetitorUpdate, db: Session = Depends(get_db)):
    c = db.get(Competitor, competitor_id)
    if not c:
        raise HTTPException(status_code=404, detail="Competitor not found")
    for field, value in updates.model_dump(exclude_none=True).items():
        setattr(c, field, value)
    db.commit()
    return _load(db, competitor_id)


@router.delete("/{competitor_id}", status_code=204)
def delete_competitor(competitor_id: int, db: Session = Depends(get_db)):
    c = db.get(Competitor, competitor_id)
    if not c:
        raise HTTPException(status_code=404, detail="Competitor not found")
    db.delete(c)
    db.commit()


# ── Menu Items ────────────────────────────────────────────────────────────────

@router.post("/{competitor_id}/menu", response_model=CompetitorMenuItemOut, status_code=201)
def add_menu_item(competitor_id: int, data: CompetitorMenuItemCreate, db: Session = Depends(get_db)):
    if not db.get(Competitor, competitor_id):
        raise HTTPException(status_code=404, detail="Competitor not found")
    item = CompetitorMenuItem(competitor_id=competitor_id, **data.model_dump())
    db.add(item)
    # mark survey date
    db.get(Competitor, competitor_id).last_surveyed = datetime.utcnow()
    db.commit()
    db.refresh(item)
    return item


@router.get("/{competitor_id}/menu", response_model=List[CompetitorMenuItemOut])
def list_menu_items(
    competitor_id: int,
    category: Optional[MenuCategory] = Query(None),
    db: Session = Depends(get_db),
):
    if not db.get(Competitor, competitor_id):
        raise HTTPException(status_code=404, detail="Competitor not found")
    q = db.query(CompetitorMenuItem).filter(CompetitorMenuItem.competitor_id == competitor_id)
    if category:
        q = q.filter(CompetitorMenuItem.category == category)
    return q.order_by(CompetitorMenuItem.category, CompetitorMenuItem.name).all()


@router.patch("/{competitor_id}/menu/{item_id}", response_model=CompetitorMenuItemOut)
def update_menu_item(
    competitor_id: int, item_id: int, updates: CompetitorMenuItemUpdate, db: Session = Depends(get_db)
):
    item = db.query(CompetitorMenuItem).filter(
        CompetitorMenuItem.id == item_id,
        CompetitorMenuItem.competitor_id == competitor_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    for field, value in updates.model_dump(exclude_none=True).items():
        setattr(item, field, value)
    item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{competitor_id}/menu/{item_id}", status_code=204)
def delete_menu_item(competitor_id: int, item_id: int, db: Session = Depends(get_db)):
    item = db.query(CompetitorMenuItem).filter(
        CompetitorMenuItem.id == item_id,
        CompetitorMenuItem.competitor_id == competitor_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    db.delete(item)
    db.commit()


def _load(db: Session, competitor_id: int):
    return (
        db.query(Competitor)
        .options(joinedload(Competitor.menu_items))
        .filter(Competitor.id == competitor_id)
        .first()
    )
