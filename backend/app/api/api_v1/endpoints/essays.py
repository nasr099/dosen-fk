from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.deps import get_current_admin_user, get_current_staff_user
from app.db.base import get_db
from app.db.models import ExamAnswer, ExamSession, Question, QuestionSet, User, EssayGrade
from app.schemas.exam import EssayAnswerItem, EssayGradePayload, EssayGradePublic, EssayListResponse

router = APIRouter()

@router.get("/essays", response_model=EssayListResponse)
def list_essays(
    status: str = Query("pending", regex="^(pending|graded)$"),
    q: Optional[str] = None,
    set_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    _=Depends(get_current_staff_user),
):
    # Base join across answers, questions (to filter by essay), session, user, set
    base_select = (
        db.query(
            ExamAnswer.id.label("answer_id"),
            ExamSession.id.label("session_id"),
            User.id.label("user_id"),
            User.email.label("user_email"),
            QuestionSet.id.label("set_id"),
            QuestionSet.title.label("set_title"),
            Question.id.label("question_id"),
            Question.question_text.label("question_text"),
            ExamAnswer.selected_answer.label("user_answer"),
            ExamSession.completed_at.label("completed_at"),
        )
        .join(ExamSession, ExamAnswer.exam_session_id == ExamSession.id)
        .join(Question, ExamAnswer.question_id == Question.id)
        .join(User, ExamSession.user_id == User.id)
        .outerjoin(QuestionSet, Question.question_set_id == QuestionSet.id)
        .filter((Question.question_type == "essay"))
    )

    count_q = (
        db.query(ExamAnswer.id)
        .join(ExamSession, ExamAnswer.exam_session_id == ExamSession.id)
        .join(Question, ExamAnswer.question_id == Question.id)
        .outerjoin(QuestionSet, Question.question_set_id == QuestionSet.id)
        .join(User, ExamSession.user_id == User.id)
        .filter((Question.question_type == "essay"))
    )

    def apply_filters(qry, is_count=False):
        if set_id:
            qry = qry.filter(QuestionSet.id == set_id)
        if q:
            like = f"%{q.strip()}%"
            qry = qry.filter((Question.question_text.ilike(like)) | (User.email.ilike(like)))
        if status == "graded":
            qry = qry.join(EssayGrade, EssayGrade.exam_answer_id == ExamAnswer.id)
        else:
            qry = qry.outerjoin(EssayGrade, EssayGrade.exam_answer_id == ExamAnswer.id).filter(EssayGrade.id.is_(None))
        return qry

    base_select = apply_filters(base_select).order_by(ExamSession.completed_at.desc().nullslast())
    count_q = apply_filters(count_q, is_count=True)

    total = count_q.count()
    items = base_select.offset((page - 1) * page_size).limit(page_size).all()

    # fetch grades for those that exist
    answer_ids = [row.answer_id for row in items]
    grades_map = {}
    if answer_ids:
        for g in db.query(EssayGrade).filter(EssayGrade.exam_answer_id.in_(answer_ids)).all():
            grades_map[g.exam_answer_id] = g

    result: List[EssayAnswerItem] = []
    for row in items:
        g = grades_map.get(row.answer_id)
        grade = None
        if g:
            grade = EssayGradePublic.from_orm(g)
        result.append(EssayAnswerItem(
            answer_id=row.answer_id,
            session_id=row.session_id,
            user_id=row.user_id,
            user_email=row.user_email,
            set_id=row.set_id,
            set_title=row.set_title,
            question_id=row.question_id,
            question_text=row.question_text,
            user_answer=row.user_answer,
            completed_at=row.completed_at,
            grade=grade,
        ))
    return {"total": total, "items": result}


@router.put("/essays/{answer_id}", response_model=EssayGradePublic)
def grade_essay(
    answer_id: int,
    payload: EssayGradePayload,
    db: Session = Depends(get_db),
    admin = Depends(get_current_staff_user),
):
    # Verify answer exists and is essay
    ans = db.query(ExamAnswer).filter(ExamAnswer.id == answer_id).first()
    if not ans:
        raise HTTPException(status_code=404, detail="Answer not found")
    q = db.query(Question).filter(Question.id == ans.question_id).first()
    if not q or (q.question_type or "mcq") != "essay":
        raise HTTPException(status_code=400, detail="Not an essay answer")

    # Clamp score and auto-derive status
    score = max(0, min(100, int(payload.score)))
    if score >= 70:
        status = "approved"
    elif score >= 40:
        status = "partial"
    else:
        status = "incorrect"

    grade = db.query(EssayGrade).filter(EssayGrade.exam_answer_id == answer_id).first()
    if not grade:
        grade = EssayGrade(exam_answer_id=answer_id)
        db.add(grade)
    grade.score = score
    grade.status = status
    grade.notes = (payload.notes or None)
    grade.graded_by = getattr(admin, 'id', None)
    db.commit()
    db.refresh(grade)
    return grade
