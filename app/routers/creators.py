from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import ContentCreator
from app.schemas import CreatorCreate, CreatorOut, CreatorUpdate

router = APIRouter(prefix="/creators", tags=["creators"])


@router.post("/", response_model=CreatorOut, status_code=201)
def create_creator(creator: CreatorCreate, db: Session = Depends(get_db)):
    db_creator = ContentCreator(**creator.model_dump())
    db.add(db_creator)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered")
    db.refresh(db_creator)
    return db_creator


@router.get("/", response_model=List[CreatorOut])
def list_creators(db: Session = Depends(get_db)):
    return db.query(ContentCreator).all()


@router.get("/{creator_id}", response_model=CreatorOut)
def get_creator(creator_id: int, db: Session = Depends(get_db)):
    creator = db.get(ContentCreator, creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")
    return creator


@router.patch("/{creator_id}", response_model=CreatorOut)
def update_creator(creator_id: int, updates: CreatorUpdate, db: Session = Depends(get_db)):
    creator = db.get(ContentCreator, creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")
    for field, value in updates.model_dump(exclude_none=True).items():
        setattr(creator, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered")
    db.refresh(creator)
    return creator


@router.delete("/{creator_id}", status_code=204)
def delete_creator(creator_id: int, db: Session = Depends(get_db)):
    creator = db.get(ContentCreator, creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")
    db.delete(creator)
    db.commit()
