from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_current_admin_user
from app.db.base import get_db
from app.db.models import PromoBanner as PromoModel
from app.schemas.exam import PromoBannerCreate, PromoBannerUpdate, PromoBanner as PromoSchema

router = APIRouter()

@router.get("/", response_model=List[PromoSchema])
def list_active_promos(db: Session = Depends(get_db)):
    return db.query(PromoModel).filter(PromoModel.is_active == True).order_by(PromoModel.display_order.asc()).all()

@router.post("/", response_model=PromoSchema)
def create_promo(
    promo_in: PromoBannerCreate,
    db: Session = Depends(get_db),
    admin_user=Depends(get_current_admin_user),
):
    promo = PromoModel(**promo_in.model_dump())
    db.add(promo)
    db.commit()
    db.refresh(promo)
    return promo

@router.put("/{promo_id}", response_model=PromoSchema)
def update_promo(
    promo_id: int,
    promo_in: PromoBannerUpdate,
    db: Session = Depends(get_db),
    admin_user=Depends(get_current_admin_user),
):
    promo = db.query(PromoModel).filter(PromoModel.id == promo_id).first()
    if not promo:
        raise HTTPException(status_code=404, detail="Promo not found")
    for k, v in promo_in.model_dump(exclude_unset=True).items():
        setattr(promo, k, v)
    db.commit()
    db.refresh(promo)
    return promo

@router.delete("/{promo_id}")
def delete_promo(
    promo_id: int, db: Session = Depends(get_db), admin_user=Depends(get_current_admin_user)
):
    promo = db.query(PromoModel).filter(PromoModel.id == promo_id).first()
    if not promo:
        raise HTTPException(status_code=404, detail="Promo not found")
    db.delete(promo)
    db.commit()
    return {"message": "Promo deleted"}
