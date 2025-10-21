from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.deps import get_current_admin_user
from app.db.base import get_db
from app.db.models import (
    QuestionSet as QuestionSetModel,
    Category as CategoryModel,
    Question as QuestionModel,
    ExamSession as ExamSessionModel,
    ExamAnswer as ExamAnswerModel,
)
from app.schemas.set import (
    QuestionSet as QuestionSetSchema,
    QuestionSetCreate,
    QuestionSetUpdate,
    QuestionSetWithQuestionsCreate,
    QuestionSetWithQuestionsUpdate,
)

router = APIRouter()

@router.get("/", response_model=List[QuestionSetSchema])
def list_sets(
    db: Session = Depends(get_db),
    category_id: Optional[int] = Query(None)
):
    q = db.query(QuestionSetModel).filter(QuestionSetModel.is_active == True)
    if category_id is not None:
        q = q.filter(QuestionSetModel.category_id == category_id)
    return q.order_by(QuestionSetModel.created_at.desc()).all()

@router.get("/{set_id}", response_model=QuestionSetSchema)
def get_set(set_id: int, db: Session = Depends(get_db)):
    s = db.query(QuestionSetModel).filter(QuestionSetModel.id == set_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Set not found")
    return s

@router.put("/{set_id}/with-questions", response_model=QuestionSetSchema)
def update_set_with_questions(
    set_id: int,
    payload: QuestionSetWithQuestionsUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin_user),
):
    s = db.query(QuestionSetModel).filter(QuestionSetModel.id == set_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Set not found")

    # update set fields
    for k, v in payload.model_dump(exclude_unset=True, exclude={"questions"}).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)

    # replace questions belonging to this set
    # First, delete exam_answers that reference existing questions in this set
    q_sub = db.query(QuestionModel.id).filter(QuestionModel.question_set_id == set_id).subquery()
    db.query(ExamAnswerModel).filter(ExamAnswerModel.question_id.in_(q_sub)).delete(synchronize_session=False)
    db.commit()
    # Then remove questions in this set
    db.query(QuestionModel).filter(QuestionModel.question_set_id == set_id).delete(synchronize_session=False)
    db.commit()
    for q in payload.questions:
        db.add(QuestionModel(
            category_id=s.category_id,
            question_set_id=set_id,
            question_text=q.question_text,
            option_a=q.option_a,
            option_b=q.option_b,
            option_c=q.option_c,
            option_d=q.option_d,
            option_e=q.option_e,
            correct_answer=q.correct_answer,
            explanation=q.explanation,
            is_featured=q.is_featured,
            difficulty_level=q.difficulty_level or 'medium',
        ))
    db.commit()
    db.refresh(s)
    return s

@router.post("/with-questions", response_model=QuestionSetSchema)
def create_set_with_questions(
    payload: QuestionSetWithQuestionsCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin_user)
):
    # validate category
    cat = db.query(CategoryModel).filter(CategoryModel.id == payload.category_id).first()
    if not cat:
        raise HTTPException(status_code=400, detail="Invalid category")
    s = QuestionSetModel(
        category_id=payload.category_id,
        title=payload.title,
        description=payload.description,
        time_limit_minutes=payload.time_limit_minutes,
        is_active=payload.is_active,
        access_level=getattr(payload, 'access_level', 'free') or 'free',
    )
    db.add(s)
    db.commit()
    db.refresh(s)

    # create questions under this set
    for q in payload.questions:
        db.add(QuestionModel(
            category_id=payload.category_id,
            question_set_id=s.id,
            question_text=q.question_text,
            option_a=q.option_a,
            option_b=q.option_b,
            option_c=q.option_c,
            option_d=q.option_d,
            option_e=q.option_e,
            correct_answer=q.correct_answer,
            explanation=q.explanation,
            is_featured=q.is_featured,
            difficulty_level=q.difficulty_level or 'medium',
        ))
    db.commit()
    db.refresh(s)
    return s

@router.post("/", response_model=QuestionSetSchema)
def create_set(
    payload: QuestionSetCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin_user)
):
    # validate category
    cat = db.query(CategoryModel).filter(CategoryModel.id == payload.category_id).first()
    if not cat:
        raise HTTPException(status_code=400, detail="Invalid category")
    s = QuestionSetModel(**payload.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

@router.put("/{set_id}", response_model=QuestionSetSchema)
def update_set(
    set_id: int,
    payload: QuestionSetUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin_user)
):
    s = db.query(QuestionSetModel).filter(QuestionSetModel.id == set_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Set not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return s

@router.delete("/{set_id}")
def delete_set(set_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin_user)):
    s = db.query(QuestionSetModel).filter(QuestionSetModel.id == set_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Set not found")
    # 1) delete exam_answers that reference questions in this set
    q_sub = db.query(QuestionModel.id).filter(QuestionModel.question_set_id == set_id).subquery()
    db.query(ExamAnswerModel).filter(ExamAnswerModel.question_id.in_(q_sub)).delete(synchronize_session=False)
    db.commit()
    # 2) remove questions under this set to satisfy FK
    db.query(QuestionModel).filter(QuestionModel.question_set_id == set_id).delete(synchronize_session=False)
    db.commit()
    # 3) null-out exam sessions referencing this set (keep history intact)
    db.query(ExamSessionModel).filter(ExamSessionModel.question_set_id == set_id).update({ExamSessionModel.question_set_id: None})
    db.commit()
    # 4) delete the set itself
    db.delete(s)
    db.commit()
    return {"message": "Set deleted"}
