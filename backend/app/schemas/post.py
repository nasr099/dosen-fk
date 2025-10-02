from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PostBase(BaseModel):
    title: str
    slug: str
    excerpt: Optional[str] = None
    content_html: str
    cover_url: Optional[str] = None
    is_published: bool = False
    published_at: Optional[datetime] = None

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    excerpt: Optional[str] = None
    content_html: Optional[str] = None
    cover_url: Optional[str] = None
    is_published: Optional[bool] = None
    published_at: Optional[datetime] = None

class Post(PostBase):
    id: int
    author_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
