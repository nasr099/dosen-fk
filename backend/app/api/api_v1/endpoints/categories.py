from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_current_admin_user
from app.db.base import get_db
from app.db.models import (
    Category as CategoryModel,
    QuestionSet as QuestionSetModel,
    Question as QuestionModel,
    ExamSession as ExamSessionModel,
    ExamAnswer as ExamAnswerModel,
)
from app.schemas.question import CategoryCreate, CategoryUpdate, Category as CategorySchema

router = APIRouter()

@router.get("/", response_model=List[CategorySchema])
def list_categories(db: Session = Depends(get_db)):
    return db.query(CategoryModel).filter(CategoryModel.is_active == True).all()

@router.get("/heads", response_model=List[CategorySchema])
def list_head_categories(db: Session = Depends(get_db)):
    return db.query(CategoryModel).filter(CategoryModel.is_active == True, CategoryModel.parent_id == None).all()

@router.get("/{head_id}/children", response_model=List[CategorySchema])
def list_children(head_id: int, db: Session = Depends(get_db)):
    head = db.query(CategoryModel).filter(CategoryModel.id == head_id).first()
    if not head:
        raise HTTPException(status_code=404, detail="Head category not found")
    return db.query(CategoryModel).filter(CategoryModel.is_active == True, CategoryModel.parent_id == head_id).all()

@router.post("/", response_model=CategorySchema)
def create_category(
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    admin_user=Depends(get_current_admin_user),
):
    category = CategoryModel(**category_in.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category

@router.put("/{category_id}", response_model=CategorySchema)
def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    db: Session = Depends(get_db),
    admin_user=Depends(get_current_admin_user),
):
    category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    for k, v in category_in.model_dump(exclude_unset=True).items():
        setattr(category, k, v)
    db.commit()
    db.refresh(category)
    return category

@router.delete("/{category_id}")
def delete_category(
    category_id: int, db: Session = Depends(get_db), admin_user=Depends(get_current_admin_user)
):
    category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    # Collect set ids in this category
    set_ids_sub = db.query(QuestionSetModel.id).filter(QuestionSetModel.category_id == category_id).subquery()

    # A) delete exam sessions that belong to this category (by category_id) or reference its sets
    session_ids_sub = db.query(ExamSessionModel.id).filter(
        (ExamSessionModel.category_id == category_id) |
        (ExamSessionModel.question_set_id.in_(set_ids_sub))
    ).subquery()

    # A1) delete exam_answers belonging to those sessions
    db.query(ExamAnswerModel).filter(ExamAnswerModel.exam_session_id.in_(session_ids_sub)).delete(synchronize_session=False)
    db.commit()
    # A2) delete those sessions
    db.query(ExamSessionModel).filter(ExamSessionModel.id.in_(session_ids_sub)).delete(synchronize_session=False)
    db.commit()

    # B) delete exam_answers that reference questions in this category (safety)
    q_sub = db.query(QuestionModel.id).filter(QuestionModel.category_id == category_id).subquery()
    db.query(ExamAnswerModel).filter(ExamAnswerModel.question_id.in_(q_sub)).delete(synchronize_session=False)
    db.commit()

    # C) delete questions in this category
    db.query(QuestionModel).filter(QuestionModel.category_id == category_id).delete(synchronize_session=False)
    db.commit()

    # D) delete question sets under this category
    db.query(QuestionSetModel).filter(QuestionSetModel.category_id == category_id).delete(synchronize_session=False)
    db.commit()

    # E) delete the category itself
    db.delete(category)
    db.commit()
    return {"message": "Category deleted"}
