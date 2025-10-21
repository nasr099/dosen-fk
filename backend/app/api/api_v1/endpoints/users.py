from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.api.deps import get_current_active_user, get_current_admin_user
from app.db.base import get_db
from app.db.models import User as UserModel
from app.schemas.user import User as UserSchema

router = APIRouter()

@router.get("/me", response_model=UserSchema)
def read_users_me(current_user: UserModel = Depends(get_current_active_user)):
    return current_user

@router.get("/", response_model=List[UserSchema])
def list_users(
    db: Session = Depends(get_db), admin_user: UserModel = Depends(get_current_admin_user)
):
    # order by created desc for convenience
    return db.query(UserModel).order_by(UserModel.created_at.desc()).all()

@router.get("/{user_id}", response_model=UserSchema)
def get_user(user_id: int, db: Session = Depends(get_db), admin_user: UserModel = Depends(get_current_admin_user)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/{user_id}/activate", response_model=UserSchema)
def activate_user(user_id: int, db: Session = Depends(get_db), admin_user: UserModel = Depends(get_current_admin_user)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Activate for 1 month (approx 30 days)
    now = datetime.now(timezone.utc)
    # When activating, mark as paid; trigger will set is_active accordingly
    try:
        user.plan = 'paid'
    except Exception:
        pass
    user.active_until = now + timedelta(days=30)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# ---------------- Plan (Free/Paid) ----------------
class PlanPayload(BaseModel):
    plan: str  # 'free' | 'paid'

@router.patch("/{user_id}/plan", response_model=UserSchema)
def update_plan(user_id: int, payload: PlanPayload, db: Session = Depends(get_db), admin_user: UserModel = Depends(get_current_admin_user)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    plan = (payload.plan or 'free').lower()
    if plan not in ('free','paid'):
        raise HTTPException(status_code=400, detail="Invalid plan")
    user.plan = plan
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

class BulkPlanPayload(BaseModel):
    ids: List[int]
    plan: str  # 'free' | 'paid'

@router.post("/set-plan-bulk", response_model=List[UserSchema])
def set_plan_bulk(payload: BulkPlanPayload, db: Session = Depends(get_db), admin_user: UserModel = Depends(get_current_admin_user)):
    ids = list(set(int(i) for i in (payload.ids or [])))
    if not ids:
        return []
    plan = (payload.plan or 'free').lower()
    if plan not in ('free','paid'):
        raise HTTPException(status_code=400, detail="Invalid plan")
    users = db.query(UserModel).filter(UserModel.id.in_(ids)).all()
    for u in users:
        u.plan = plan
        db.add(u)
    db.commit()
    for u in users:
        db.refresh(u)
    return users

# ---------------- Bulk Operations ----------------
class IdsPayload(BaseModel):
    ids: List[int]
    months: Optional[int] = 1

@router.post("/activate-bulk", response_model=List[UserSchema])
def activate_bulk(payload: IdsPayload, db: Session = Depends(get_db), admin_user: UserModel = Depends(get_current_admin_user)):
    ids = list(set(int(i) for i in (payload.ids or [])))
    if not ids:
        return []
    now = datetime.now(timezone.utc)
    delta = timedelta(days=30 * (payload.months or 1))
    users = db.query(UserModel).filter(UserModel.id.in_(ids)).all()
    for u in users:
        u.active_until = now + delta
        try:
            u.plan = 'paid'
        except Exception:
            pass
        db.add(u)
    db.commit()
    for u in users:
        db.refresh(u)
    return users

@router.post("/deactivate-bulk", response_model=List[UserSchema])
def deactivate_bulk(payload: IdsPayload, db: Session = Depends(get_db), admin_user: UserModel = Depends(get_current_admin_user)):
    ids = list(set(int(i) for i in (payload.ids or [])))
    if not ids:
        return []
    users = db.query(UserModel).filter(UserModel.id.in_(ids)).all()
    for u in users:
        try:
            u.plan = 'free'
        except Exception:
            pass
        # Clear validity date when switching to free plan
        u.active_until = None
        db.add(u)
    db.commit()
    for u in users:
        db.refresh(u)
    return users

@router.post("/{user_id}/deactivate", response_model=UserSchema)
def deactivate_user(user_id: int, db: Session = Depends(get_db), admin_user: UserModel = Depends(get_current_admin_user)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        user.plan = 'free'
    except Exception:
        pass
    # Clear validity date when switching to free plan
    user.active_until = None
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
