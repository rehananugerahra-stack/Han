from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import Promotion, PromoType, Venue
from app.schemas import PromotionCreate, PromotionOut, PromotionUpdate

router = APIRouter(prefix="/promotions", tags=["promotions"])


@router.post("/", response_model=PromotionOut, status_code=201)
def create_promotion(promo: PromotionCreate, db: Session = Depends(get_db)):
    if promo.venue_id and not db.get(Venue, promo.venue_id):
        raise HTTPException(status_code=404, detail="Venue not found")
    if not promo.discount_percent and not promo.discount_amount:
        raise HTTPException(status_code=422, detail="Provide discount_percent or discount_amount")
    db_promo = Promotion(**promo.model_dump())
    db.add(db_promo)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Promo code already exists")
    db.refresh(db_promo)
    return db_promo


@router.get("/", response_model=List[PromotionOut])
def list_promotions(
    promo_type: Optional[PromoType] = Query(None),
    active_only: bool = Query(False),
    venue_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Promotion)
    if promo_type:
        q = q.filter(Promotion.promo_type == promo_type)
    if active_only:
        q = q.filter(Promotion.is_active == True)  # noqa: E712
    if venue_id:
        q = q.filter(Promotion.venue_id == venue_id)
    return q.all()


@router.get("/validate/{code}", response_model=PromotionOut)
def validate_code(code: str, db: Session = Depends(get_db)):
    from datetime import datetime
    promo = db.query(Promotion).filter(Promotion.code == code).first()
    if not promo:
        raise HTTPException(status_code=404, detail="Promo code not found")
    now = datetime.utcnow()
    if not promo.is_active:
        raise HTTPException(status_code=410, detail="Promo code is inactive")
    if now < promo.valid_from or now > promo.valid_until:
        raise HTTPException(status_code=410, detail="Promo code is expired or not yet valid")
    if promo.max_usage and promo.usage_count >= promo.max_usage:
        raise HTTPException(status_code=410, detail="Promo code usage limit reached")
    return promo


@router.post("/redeem/{code}", response_model=PromotionOut)
def redeem_code(code: str, db: Session = Depends(get_db)):
    promo = validate_code(code, db)
    promo.usage_count += 1
    if promo.max_usage and promo.usage_count >= promo.max_usage:
        promo.is_active = False
    db.commit()
    db.refresh(promo)
    return promo


@router.get("/{promo_id}", response_model=PromotionOut)
def get_promotion(promo_id: int, db: Session = Depends(get_db)):
    promo = db.get(Promotion, promo_id)
    if not promo:
        raise HTTPException(status_code=404, detail="Promotion not found")
    return promo


@router.patch("/{promo_id}", response_model=PromotionOut)
def update_promotion(promo_id: int, updates: PromotionUpdate, db: Session = Depends(get_db)):
    promo = db.get(Promotion, promo_id)
    if not promo:
        raise HTTPException(status_code=404, detail="Promotion not found")
    for field, value in updates.model_dump(exclude_none=True).items():
        setattr(promo, field, value)
    db.commit()
    db.refresh(promo)
    return promo


@router.delete("/{promo_id}", status_code=204)
def delete_promotion(promo_id: int, db: Session = Depends(get_db)):
    promo = db.get(Promotion, promo_id)
    if not promo:
        raise HTTPException(status_code=404, detail="Promotion not found")
    db.delete(promo)
    db.commit()
