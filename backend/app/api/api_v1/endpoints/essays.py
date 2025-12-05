from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import literal
from sqlalchemy.sql import func
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
    is_tryout: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    _=Depends(get_current_staff_user),
):
    # --- Auto-grade blank essays with 0 (incorrect) so they don't appear in grading queue ---
    # Exams
    blank_exam = (
        db.query(ExamAnswer.id)
        .join(Question, ExamAnswer.question_id == Question.id)
        .outerjoin(EssayGrade, EssayGrade.exam_answer_id == ExamAnswer.id)
        .filter(Question.question_type == "essay")
        .filter((ExamAnswer.selected_answer.is_(None)) | (func.trim(ExamAnswer.selected_answer) == ""))
        .filter(EssayGrade.id.is_(None))
        .all()
    )
    if blank_exam:
        for row in blank_exam:
            g = EssayGrade(exam_answer_id=row.id, score=0, status="incorrect")
            db.add(g)
        db.commit()
    # Tryouts
    from app.db.models import TryoutAnswer as TryoutAnswerModel
    blank_try = (
        db.query(TryoutAnswerModel.id)
        .join(Question, TryoutAnswerModel.question_id == Question.id)
        .outerjoin(EssayGrade, EssayGrade.tryout_answer_id == TryoutAnswerModel.id)
        .filter(Question.question_type == "essay")
        .filter((TryoutAnswerModel.selected_answer.is_(None)) | (func.trim(TryoutAnswerModel.selected_answer) == ""))
        .filter(EssayGrade.id.is_(None))
        .all()
    )
    if blank_try:
        for row in blank_try:
            g = EssayGrade(tryout_answer_id=row.id, score=0, status="incorrect")
            db.add(g)
        db.commit()
    # EXAM essays
    exam_q = (
        db.query(
            ExamAnswer.id.label("answer_id"),
            ExamSession.id.label("session_id"),
            User.id.label("user_id"),
            User.email.label("user_email"),
            User.full_name.label("user_full_name"),
            QuestionSet.id.label("set_id"),
            QuestionSet.title.label("set_title"),
            Question.id.label("question_id"),
            Question.question_text.label("question_text"),
            ExamAnswer.selected_answer.label("user_answer"),
            ExamSession.completed_at.label("completed_at"),
            literal(False).label("is_tryout"),
        )
        .join(ExamSession, ExamAnswer.exam_session_id == ExamSession.id)
        .join(Question, ExamAnswer.question_id == Question.id)
        .join(User, ExamSession.user_id == User.id)
        .outerjoin(QuestionSet, Question.question_set_id == QuestionSet.id)
        .filter((Question.question_type == "essay"))
    )
    # TRYOUT essays
    from app.db.models import TryoutAnswer, TryoutSetSession, TryoutSession
    tryout_q = (
        db.query(
            TryoutAnswer.id.label("answer_id"),
            TryoutSession.id.label("session_id"),
            User.id.label("user_id"),
            User.email.label("user_email"),
            User.full_name.label("user_full_name"),
            QuestionSet.id.label("set_id"),
            QuestionSet.title.label("set_title"),
            Question.id.label("question_id"),
            Question.question_text.label("question_text"),
            TryoutAnswer.selected_answer.label("user_answer"),
            TryoutSetSession.run_end_at.label("completed_at"),
            literal(True).label("is_tryout"),
        )
        .join(TryoutSetSession, TryoutAnswer.tryout_set_session_id == TryoutSetSession.id)
        .join(TryoutSession, TryoutSetSession.tryout_session_id == TryoutSession.id)
        .join(User, TryoutSession.user_id == User.id)
        .join(Question, TryoutAnswer.question_id == Question.id)
        .outerjoin(QuestionSet, Question.question_set_id == QuestionSet.id)
        .filter((Question.question_type == "essay"))
    )

    def apply_filters_exam(qry):
        if set_id:
            qry = qry.filter(QuestionSet.id == set_id)
        if q:
            like = f"%{q.strip()}%"
            qry = qry.filter(
                (Question.question_text.ilike(like)) |
                (User.email.ilike(like)) |
                (User.full_name.ilike(like))
            )
        if status == "graded":
            qry = qry.join(EssayGrade, EssayGrade.exam_answer_id == ExamAnswer.id)
        else:
            qry = qry.outerjoin(EssayGrade, EssayGrade.exam_answer_id == ExamAnswer.id).filter(EssayGrade.id.is_(None))
        # Only show essays with non-empty answers
        qry = qry.filter(ExamAnswer.selected_answer.isnot(None)).filter(func.trim(ExamAnswer.selected_answer) != "")
        return qry

    def apply_filters_tryout(qry):
        if set_id:
            qry = qry.filter(QuestionSet.id == set_id)
        if q:
            like = f"%{q.strip()}%"
            qry = qry.filter(
                (Question.question_text.ilike(like)) |
                (User.email.ilike(like)) |
                (User.full_name.ilike(like))
            )
        if status == "graded":
            qry = qry.join(EssayGrade, EssayGrade.tryout_answer_id == TryoutAnswer.id)
        else:
            qry = qry.outerjoin(EssayGrade, EssayGrade.tryout_answer_id == TryoutAnswer.id).filter(EssayGrade.id.is_(None))
        # Only show essays with non-empty answers
        qry = qry.filter(TryoutAnswer.selected_answer.isnot(None)).filter(func.trim(TryoutAnswer.selected_answer) != "")
        return qry

    items = []
    total = 0
    if is_tryout is True:
        from app.db.models import TryoutSetSession as TSS
        tq = apply_filters_tryout(tryout_q).order_by(TSS.run_end_at.desc().nullslast())
        total = tq.count()
        items = tq.offset((page - 1) * page_size).limit(page_size).all()
    elif is_tryout is False:
        eq = apply_filters_exam(exam_q).order_by(ExamSession.completed_at.desc().nullslast())
        total = eq.count()
        items = eq.offset((page - 1) * page_size).limit(page_size).all()
    else:
        # both: simple union by fetching limited from each (basic pagination)
        from app.db.models import TryoutSetSession as TSS
        eq = apply_filters_exam(exam_q)
        tq = apply_filters_tryout(tryout_q)
        total = eq.count() + tq.count()
        items = (
            eq.order_by(ExamSession.completed_at.desc().nullslast()).limit(page_size//2).all() +
            tq.order_by(TSS.run_end_at.desc().nullslast()).limit(page_size - (page_size//2)).all()
        )

    # Map grades
    result: List[EssayAnswerItem] = []
    exam_ids = [r.answer_id for r in items if not r.is_tryout]
    tryout_ids = [r.answer_id for r in items if r.is_tryout]
    grades_map = {}
    if exam_ids:
        for g in db.query(EssayGrade).filter(EssayGrade.exam_answer_id.in_(exam_ids)).all():
            grades_map[('exam', g.exam_answer_id)] = g
    if tryout_ids:
        for g in db.query(EssayGrade).filter(EssayGrade.tryout_answer_id.in_(tryout_ids)).all():
            grades_map[('tryout', g.tryout_answer_id)] = g

    for row in items:
        key = ('tryout', row.answer_id) if row.is_tryout else ('exam', row.answer_id)
        g = grades_map.get(key)
        grade = EssayGradePublic.from_orm(g) if g else None
        result.append(EssayAnswerItem(
            answer_id=row.answer_id,
            session_id=row.session_id,
            user_id=row.user_id,
            user_email=row.user_email,
            user_full_name=getattr(row, 'user_full_name', None),
            set_id=row.set_id,
            set_title=row.set_title,
            question_id=row.question_id,
            question_text=row.question_text,
            user_answer=row.user_answer,
            completed_at=row.completed_at,
            grade=grade,
            is_tryout=bool(row.is_tryout),
        ))
    return { 'total': total, 'items': [item.model_dump() for item in result] }


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

@router.put("/essays/tryout/{answer_id}", response_model=EssayGradePublic)
def grade_tryout_essay(
    answer_id: int,
    payload: EssayGradePayload,
    db: Session = Depends(get_db),
    admin = Depends(get_current_staff_user),
):
    from app.db.models import TryoutAnswer
    ans = db.query(TryoutAnswer).filter(TryoutAnswer.id == answer_id).first()
    if not ans:
        raise HTTPException(status_code=404, detail="Tryout answer not found")
    # No question type enforcement here (assume UI filtered essays)
    score = max(0, min(100, int(payload.score)))
    status = "approved" if score >= 70 else ("partial" if score >= 40 else "incorrect")
    grade = db.query(EssayGrade).filter(EssayGrade.tryout_answer_id == answer_id).first()
    if not grade:
        grade = EssayGrade(tryout_answer_id=answer_id)
        db.add(grade)
    grade.score = score
    grade.status = status
    grade.notes = (payload.notes or None)
    grade.graded_by = getattr(admin, 'id', None)
    db.commit()
    db.refresh(grade)
    return grade
