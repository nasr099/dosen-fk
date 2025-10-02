from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.base import get_db
from app.api.deps import get_current_active_user
from app.db.models import TeamMember as TeamMemberModel
from app.schemas.team import TeamMember as TeamMemberSchema, TeamMemberCreate, TeamMemberUpdate, ReorderPayload

router = APIRouter()

@router.get('/', response_model=List[TeamMemberSchema])
def list_public(db: Session = Depends(get_db)):
    items = db.query(TeamMemberModel).filter(TeamMemberModel.is_visible == True).order_by(TeamMemberModel.display_order.asc(), TeamMemberModel.id.asc()).all()
    return items

@router.get('/all', response_model=List[TeamMemberSchema])
def list_all(db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail='Not authorized')
    return db.query(TeamMemberModel).order_by(TeamMemberModel.display_order.asc(), TeamMemberModel.id.asc()).all()

@router.post('/', response_model=TeamMemberSchema)
def create(payload: TeamMemberCreate, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail='Not authorized')
    item = TeamMemberModel(**payload.dict())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.put('/{member_id}', response_model=TeamMemberSchema)
def update(member_id: int, payload: TeamMemberUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail='Not authorized')
    item = db.query(TeamMemberModel).filter(TeamMemberModel.id == member_id).first()
    if not item:
        raise HTTPException(status_code=404, detail='Not found')
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item

@router.delete('/{member_id}')
def delete(member_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail='Not authorized')
    item = db.query(TeamMemberModel).filter(TeamMemberModel.id == member_id).first()
    if not item:
        raise HTTPException(status_code=404, detail='Not found')
    db.delete(item)
    db.commit()
    return { 'ok': True }

@router.post('/reorder')
def reorder(payload: ReorderPayload, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail='Not authorized')
    for idx, mid in enumerate(payload.ids):
        db.query(TeamMemberModel).filter(TeamMemberModel.id == mid).update({ 'display_order': idx })
    db.commit()
    return { 'ok': True }
