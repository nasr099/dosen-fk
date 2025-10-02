from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.deps import get_current_admin_user
from app.db.base import get_db
from app.db.models import Question as QuestionModel, Category as CategoryModel
from app.schemas.question import (
    QuestionCreate,
    QuestionUpdate,
    Question as QuestionSchema,
)

router = APIRouter()

@router.get("/", response_model=List[QuestionSchema])
def list_questions(
    db: Session = Depends(get_db),
    category_id: Optional[int] = Query(None),
    question_set_id: Optional[int] = Query(None),
    featured: Optional[bool] = Query(None),
):
    q = db.query(QuestionModel).filter(QuestionModel.is_active == True)
    if category_id is not None:
        q = q.filter(QuestionModel.category_id == category_id)
    if question_set_id is not None:
        q = q.filter(QuestionModel.question_set_id == question_set_id)
    if featured is not None:
        q = q.filter(QuestionModel.is_featured == featured)
    return q.all()

@router.post("/", response_model=QuestionSchema)
def create_question(
    question_in: QuestionCreate,
    db: Session = Depends(get_db),
    admin_user=Depends(get_current_admin_user),
):
    # validate category exists
    category = db.query(CategoryModel).filter(CategoryModel.id == question_in.category_id).first()
    if not category:
        raise HTTPException(status_code=400, detail="Invalid category")
    question = QuestionModel(**question_in.model_dump())
    db.add(question)
    db.commit()
    db.refresh(question)
    return question

@router.put("/{question_id}", response_model=QuestionSchema)
def update_question(
    question_id: int,
    question_in: QuestionUpdate,
    db: Session = Depends(get_db),
    admin_user=Depends(get_current_admin_user),
):
    question = db.query(QuestionModel).filter(QuestionModel.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    for k, v in question_in.model_dump(exclude_unset=True).items():
        setattr(question, k, v)
    db.commit()
    db.refresh(question)
    return question

@router.delete("/{question_id}")
def delete_question(
    question_id: int, db: Session = Depends(get_db), admin_user=Depends(get_current_admin_user)
):
    question = db.query(QuestionModel).filter(QuestionModel.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    db.delete(question)
    db.commit()
    return {"message": "Question deleted"}
