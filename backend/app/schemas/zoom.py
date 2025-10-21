from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ZoomDiscussionBase(BaseModel):
    title: str
    presenter_name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    start_at: datetime
    end_at: Optional[datetime] = None
    category_id: Optional[int] = None

class ZoomDiscussionCreate(ZoomDiscussionBase):
    meeting_url: Optional[str] = None
    meeting_password: Optional[str] = None

class ZoomDiscussionUpdate(BaseModel):
    title: Optional[str] = None
    presenter_name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    category_id: Optional[int] = None
    meeting_url: Optional[str] = None
    meeting_password: Optional[str] = None

class ZoomDiscussionPublic(ZoomDiscussionBase):
    id: int
    status: str  # Upcoming | Finished
    class Config:
        from_attributes = True

class ZoomDiscussion(ZoomDiscussionBase):
    id: int
    meeting_url: Optional[str] = None
    meeting_password: Optional[str] = None
    class Config:
        from_attributes = True
