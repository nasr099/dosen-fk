from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TeamMemberBase(BaseModel):
    name: str
    role: str
    headline: Optional[str] = None  # rich text (HTML)
    quote: Optional[str] = None     # rich text (HTML)
    photo_url: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    website: Optional[str] = None
    is_visible: Optional[bool] = True
    display_order: Optional[int] = 0

class TeamMemberCreate(TeamMemberBase):
    pass

class TeamMemberUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    headline: Optional[str] = None
    quote: Optional[str] = None
    photo_url: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    website: Optional[str] = None
    is_visible: Optional[bool] = None
    display_order: Optional[int] = None

class TeamMember(TeamMemberBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ReorderPayload(BaseModel):
    ids: List[int]
