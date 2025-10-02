from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
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
    return db.query(UserModel).all()

@router.get("/{user_id}", response_model=UserSchema)
def get_user(user_id: int, db: Session = Depends(get_db), admin_user: UserModel = Depends(get_current_admin_user)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
