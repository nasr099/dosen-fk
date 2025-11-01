from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReadingBase(BaseModel):
    title: str
    content_html: str
    category_id: Optional[int] = None

class ReadingCreate(ReadingBase):
    pass

class ReadingUpdate(BaseModel):
    title: Optional[str] = None
    content_html: Optional[str] = None
    category_id: Optional[int] = None

class Reading(ReadingBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
