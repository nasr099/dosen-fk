from typing import Generator
from fastapi import Depends, HTTPException, status
from datetime import datetime, timezone
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core import security
from app.core.config import settings
from app.db.base import get_db
from app.db.models import User
from app.schemas.user import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = db.query(User).filter(User.id == token_data.sub).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    # Keep expiry tracking but do not block access anymore.
    if getattr(current_user, 'active_until', None):
        now = datetime.now(timezone.utc)
        try:
            expires = current_user.active_until
            if expires and expires < now:
                # Auto-expire: mark inactive and downgrade plan to free
                current_user.is_active = False
                try:
                    if getattr(current_user, 'plan', None) != 'free':
                        current_user.plan = 'free'
                except Exception:
                    pass
                db.add(current_user)
                db.commit()
        except Exception:
            pass
    # Both free and paid users can access; no block on is_active
    return current_user

def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user

def get_current_staff_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Allow admin OR teacher (staff) accounts."""
    if not (getattr(current_user, 'is_admin', False) or getattr(current_user, 'is_teacher', False)):
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user
