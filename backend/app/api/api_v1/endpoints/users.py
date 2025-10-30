from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.api.deps import get_current_active_user, get_current_admin_user
from app.db.base import get_db
from app.db.models import User as UserModel
from app.schemas.user import User as UserSchema
from app.core.security import get_password_hash, verify_password
import secrets, string

router = APIRouter()

@router.get("/me", response_model=UserSchema)
def read_users_me(current_user: UserModel = Depends(get_current_active_user)):
    return current_user

# --------- Self-service password change ---------
class ChangePasswordPayload(BaseModel):
    current_password: str
    new_password: str

@router.post("/me/change-password")
def change_password_me(payload: ChangePasswordPayload, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_active_user)):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if not payload.new_password or len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
    current_user.hashed_password = get_password_hash(payload.new_password)
    db.add(current_user)
    db.commit()
    return { 'status': 'ok' }

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

# ---------------- Teacher Role ----------------
class TeacherPayload(BaseModel):
    is_teacher: bool

@router.patch("/{user_id}/teacher", response_model=UserSchema)
def set_teacher(user_id: int, payload: TeacherPayload, db: Session = Depends(get_db), admin_user: UserModel = Depends(get_current_admin_user)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_teacher = bool(payload.is_teacher)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# ---------------- Password Reset (Admin) ----------------
class ResetPasswordPayload(BaseModel):
    new_password: Optional[str] = None
    generate: Optional[bool] = False
    length: Optional[int] = 12

@router.post("/{user_id}/reset-password")
def reset_password(user_id: int, payload: ResetPasswordPayload, db: Session = Depends(get_db), admin_user: UserModel = Depends(get_current_admin_user)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Decide password to set
    temporary_password = None
    if payload.generate:
        L = max(8, min(int(payload.length or 12), 64))
        alphabet = string.ascii_letters + string.digits
        # ensure at least one of each class
        pw = [secrets.choice(string.ascii_lowercase), secrets.choice(string.ascii_uppercase), secrets.choice(string.digits)]
        pw += [secrets.choice(alphabet) for _ in range(L - len(pw))]
        secrets.SystemRandom().shuffle(pw)
        temporary_password = ''.join(pw)
        raw_password = temporary_password
    else:
        raw_password = (payload.new_password or '').strip()
        if len(raw_password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    user.hashed_password = get_password_hash(raw_password)
    db.add(user)
    db.commit()

    # Do not return plaintext unless it was generated and must be shown once to admin
    resp = { 'status': 'ok', 'user_id': user.id }
    if temporary_password is not None:
        resp['temporary_password'] = temporary_password
    return resp

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
