from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import List

from app.db.base import get_db
from app.db.models import ZoomDiscussion, User
from app.schemas.zoom import (
    ZoomDiscussionCreate, ZoomDiscussionUpdate, ZoomDiscussionPublic, ZoomDiscussion as ZoomDiscussionSchema
)
from app.api.deps import get_current_active_user, get_current_admin_user

router = APIRouter()

# Helper to compute status with GMT+7
TZ_OFFSET = timedelta(hours=7)

def compute_status(z: ZoomDiscussion) -> str:
    now = datetime.now(timezone.utc) + TZ_OFFSET
    start = (z.start_at or datetime.now(timezone.utc)) + TZ_OFFSET
    if start > now:
        return "Upcoming"
    if z.end_at:
        end = z.end_at + TZ_OFFSET
        if start <= now < end:
            return "Live"
        return "Finished" if now >= end else "Upcoming"
    # No end_at provided: treat as Finished after it has started
    return "Finished" if now >= start else "Upcoming"

@router.get("/", response_model=List[ZoomDiscussionPublic])
def list_zoom_discussions(db: Session = Depends(get_db)):
    items = db.query(ZoomDiscussion).order_by(ZoomDiscussion.start_at.desc()).all()
    out = []
    for z in items:
        status = compute_status(z)
        out.append(ZoomDiscussionPublic(
            id=z.id, title=z.title, presenter_name=z.presenter_name, description=z.description,
            image_url=z.image_url, start_at=z.start_at, end_at=z.end_at, category_id=z.category_id, status=status
        ))
    return out

@router.get("/{item_id}", response_model=ZoomDiscussionPublic)
def get_zoom_discussion(item_id: int, db: Session = Depends(get_db)):
    z = db.query(ZoomDiscussion).filter(ZoomDiscussion.id == item_id).first()
    if not z:
        raise HTTPException(status_code=404, detail="Not found")
    status = compute_status(z)
    return ZoomDiscussionPublic(
        id=z.id, title=z.title, presenter_name=z.presenter_name, description=z.description,
        image_url=z.image_url, start_at=z.start_at, end_at=z.end_at, category_id=z.category_id, status=status
    )

@router.get("/{item_id}/access", response_model=dict)
def get_zoom_access(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    z = db.query(ZoomDiscussion).filter(ZoomDiscussion.id == item_id).first()
    if not z:
        raise HTTPException(status_code=404, detail="Not found")
    if (current_user.plan or 'free') != 'paid':
        raise HTTPException(status_code=403, detail="Upgrade to access the meeting link")
    return {"meeting_url": z.meeting_url, "meeting_password": z.meeting_password}

# Admin endpoints
@router.post("/", response_model=ZoomDiscussionSchema)
def create_zoom_discussion(
    data: ZoomDiscussionCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    z = ZoomDiscussion(**data.dict())
    db.add(z)
    db.commit()
    db.refresh(z)
    return z

@router.put("/{item_id}", response_model=ZoomDiscussionSchema)
def update_zoom_discussion(
    item_id: int, data: ZoomDiscussionUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    z = db.query(ZoomDiscussion).filter(ZoomDiscussion.id == item_id).first()
    if not z:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in data.dict(exclude_unset=True).items():
        setattr(z, k, v)
    db.add(z)
    db.commit()
    db.refresh(z)
    return z

@router.delete("/{item_id}")
def delete_zoom_discussion(
    item_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    z = db.query(ZoomDiscussion).filter(ZoomDiscussion.id == item_id).first()
    if not z:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(z)
    db.commit()
    return {"ok": True}
