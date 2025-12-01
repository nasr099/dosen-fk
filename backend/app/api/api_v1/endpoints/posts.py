from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from app.api.deps import get_current_admin_user, get_current_staff_user
from app.db.base import get_db
from app.db.models import Post as PostModel
from app.schemas.post import Post as PostSchema, PostCreate, PostUpdate

router = APIRouter()

@router.get("/", response_model=List[PostSchema])
def list_posts(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    published_only: bool = Query(True)
):
    query = db.query(PostModel)
    if published_only:
        query = query.filter(PostModel.is_published == True)
    if q:
        like = f"%{q}%"
        query = query.filter(PostModel.title.ilike(like))
    items = query.order_by(PostModel.published_at.desc().nullslast(), PostModel.created_at.desc()) \
        .offset((page-1)*page_size).limit(page_size).all()
    return items

@router.get("/{slug}", response_model=PostSchema)
def get_post(slug: str, db: Session = Depends(get_db)):
    p = db.query(PostModel).filter(PostModel.slug == slug).first()
    if not p or (not p.is_published):
        raise HTTPException(status_code=404, detail="Post not found")
    return p

@router.post("/", response_model=PostSchema)
def create_post(payload: PostCreate, db: Session = Depends(get_db), admin=Depends(get_current_staff_user)):
    exists = db.query(PostModel).filter(PostModel.slug == payload.slug).first()
    if exists:
        raise HTTPException(status_code=400, detail="Slug already exists")
    p = PostModel(**payload.model_dump())
    if p.is_published and p.published_at is None:
        from datetime import datetime
        p.published_at = datetime.utcnow()
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

@router.put("/{post_id}", response_model=PostSchema)
def update_post(post_id: int, payload: PostUpdate, db: Session = Depends(get_db), admin=Depends(get_current_staff_user)):
    p = db.query(PostModel).filter(PostModel.id == post_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")
    data = payload.model_dump(exclude_unset=True)
    if "slug" in data:
        if db.query(PostModel).filter(PostModel.slug == data["slug"], PostModel.id != post_id).first():
            raise HTTPException(status_code=400, detail="Slug already exists")
    for k, v in data.items():
        setattr(p, k, v)
    if p.is_published and p.published_at is None:
        from datetime import datetime
        p.published_at = datetime.utcnow()
    db.commit()
    db.refresh(p)
    return p

@router.delete("/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db), admin=Depends(get_current_staff_user)):
    p = db.query(PostModel).filter(PostModel.id == post_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")
    db.delete(p)
    db.commit()
    return {"message": "Post deleted"}
