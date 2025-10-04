def _option_value(q, letter: str):
    if not letter:
        return None
    m = {
        'A': q.option_a,
        'B': q.option_b,
        'C': q.option_c,
        'D': q.option_d,
        'E': q.option_e,
    }
    raw = m.get((letter or '').upper())
    if not raw:
        return None
    # If stored as JSON like {"text":..., "img":...}, parse; else return plain text
    try:
        import json
        val = json.loads(raw)
        return val
    except Exception:
        return raw
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_current_active_user
from app.db.base import get_db
from app.db.models import ExamSession as ExamSessionModel, ExamAnswer as ExamAnswerModel, Question as QuestionModel, QuestionSet as QuestionSetModel
from app.schemas.exam import ExamSessionCreate, ExamSession as ExamSessionSchema, ExamSubmission, ExamResult
from sqlalchemy.sql import func

router = APIRouter()

@router.post("/start", response_model=ExamSessionSchema)
def start_exam(
    payload: ExamSessionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    # If question_set_id provided, restrict to that set and use its time limit
    qs = None
    if payload.question_set_id:
        qs = db.query(QuestionSetModel).filter(QuestionSetModel.id == payload.question_set_id).first()
        if not qs:
            raise HTTPException(status_code=400, detail="Invalid question set")
        questions = db.query(QuestionModel).filter(
            QuestionModel.question_set_id == payload.question_set_id,
            QuestionModel.is_active == True,
        ).all()
        time_limit = qs.time_limit_minutes
    else:
        # Select questions by category
        questions = db.query(QuestionModel).filter(
            QuestionModel.category_id == payload.category_id, QuestionModel.is_active == True
        ).all()
        time_limit = payload.time_limit_minutes or 60
    if not questions:
        raise HTTPException(status_code=400, detail="No questions available for this category")
    exam = ExamSessionModel(
        user_id=current_user.id,
        category_id=payload.category_id,
        question_set_id=payload.question_set_id,
        total_questions=len(questions),
        time_limit_minutes=time_limit,
        is_completed=False,
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)

    # Create placeholder answer rows
    for q in questions:
        db.add(ExamAnswerModel(exam_session_id=exam.id, question_id=q.id))
    db.commit()

    return exam

@router.post("/submit", response_model=ExamResult)
def submit_exam(
    submission: ExamSubmission,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    exam = db.query(ExamSessionModel).filter(
        ExamSessionModel.id == submission.exam_session_id,
        ExamSessionModel.user_id == current_user.id,
    ).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam session not found")
    if exam.is_completed:
        raise HTTPException(status_code=400, detail="Exam already submitted")

    correct = 0
    answers_detail = []

    # Map question id to correct answer for efficiency
    question_map = {
        q.id: q for q in db.query(QuestionModel).filter(
            QuestionModel.id.in_([a.question_id for a in submission.answers])
        ).all()
    }

    # Update answers
    for a in submission.answers:
        ans = db.query(ExamAnswerModel).filter(
            ExamAnswerModel.exam_session_id == exam.id,
            ExamAnswerModel.question_id == a.question_id,
        ).first()
        if not ans:
            continue
        q = question_map.get(a.question_id)
        is_correct = (a.selected_answer or "").upper() == (q.correct_answer or "").upper()
        ans.selected_answer = (a.selected_answer or None)
        ans.is_correct = is_correct
        if is_correct:
            correct += 1
        answers_detail.append({
            "question_id": q.id,
            "question_text": q.question_text,
            "selected_answer": a.selected_answer,
            "correct_answer": q.correct_answer,
            "is_correct": is_correct,
            "explanation": q.explanation,
            "selected_detail": _option_value(q, a.selected_answer),
            "correct_detail": _option_value(q, q.correct_answer),
        })

    # finalize exam
    exam.correct_answers = correct
    exam.score_percentage = (correct / max(1, exam.total_questions)) * 100.0
    exam.is_completed = True
    # Use database time to match started_at (server_default=func.now())
    exam.completed_at = func.now()
    exam.time_taken_minutes = submission.time_taken_minutes

    db.commit()
    db.refresh(exam)

    return ExamResult(
        exam_session_id=exam.id,
        total_questions=exam.total_questions,
        correct_answers=exam.correct_answers,
        score_percentage=exam.score_percentage,
        time_taken_minutes=exam.time_taken_minutes or 0.0,
        answers=answers_detail,
    )

@router.get("/history", response_model=List[ExamSessionSchema])
def get_history(db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    return db.query(ExamSessionModel).filter(ExamSessionModel.user_id == current_user.id).order_by(ExamSessionModel.started_at.desc()).all()

@router.get("/result/{session_id}", response_model=ExamResult)
def get_result(session_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    exam = db.query(ExamSessionModel).filter(
        ExamSessionModel.id == session_id,
        ExamSessionModel.user_id == current_user.id,
    ).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam session not found")

    # gather answers and enrich with correct answer + explanation
    answers_db = db.query(ExamAnswerModel).filter(ExamAnswerModel.exam_session_id == exam.id).all()
    qids = [a.question_id for a in answers_db]
    questions = { q.id: q for q in db.query(QuestionModel).filter(QuestionModel.id.in_(qids)).all() }
    answers_detail = []
    for a in answers_db:
        q = questions.get(a.question_id)
        if not q:
            continue
        answers_detail.append({
            "question_id": q.id,
            "question_text": q.question_text,
            "selected_answer": a.selected_answer,
            "correct_answer": q.correct_answer,
            "is_correct": a.is_correct or False,
            "explanation": q.explanation,
            "selected_detail": _option_value(q, a.selected_answer),
            "correct_detail": _option_value(q, q.correct_answer),
        })

    return ExamResult(
        exam_session_id=exam.id,
        total_questions=exam.total_questions,
        correct_answers=exam.correct_answers or 0,
        score_percentage=exam.score_percentage or 0.0,
        time_taken_minutes=exam.time_taken_minutes or 0.0,
        answers=answers_detail,
    )
