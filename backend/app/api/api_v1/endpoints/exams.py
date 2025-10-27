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
from app.db.models import ExamSession as ExamSessionModel, ExamAnswer as ExamAnswerModel, Question as QuestionModel, QuestionSet as QuestionSetModel, EssayGrade as EssayGradeModel
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
        # Access control: free users cannot start paid sets
        try:
            user_plan = getattr(current_user, 'plan', 'free') or 'free'
        except Exception:
            user_plan = 'free'
        # Use getattr for safety during rolling reloads/migrations
        if ((getattr(qs, 'access_level', 'free') or 'free') == 'paid') and user_plan == 'free':
            raise HTTPException(status_code=403, detail={"code":"PAYWALL","detail":"Paid plan required"})
        questions = db.query(QuestionModel).filter(
            QuestionModel.question_set_id == payload.question_set_id,
            QuestionModel.is_active == True,
        ).order_by(QuestionModel.id.asc()).all()
        time_limit = qs.time_limit_minutes
    else:
        # Select questions by category
        questions = db.query(QuestionModel).filter(
            QuestionModel.category_id == payload.category_id, QuestionModel.is_active == True
        ).order_by(QuestionModel.id.asc()).all()
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
    objective_total = 0  # mcq + multi
    essay_ids = []

    # Map question id to correct answer for efficiency
    question_map = {
        q.id: q for q in db.query(QuestionModel).filter(
            QuestionModel.id.in_([a.question_id for a in submission.answers])
        ).all()
    }

    # Update answers (robust even if placeholder rows were removed during a set edit)
    for a in submission.answers:
        ans = db.query(ExamAnswerModel).filter(
            ExamAnswerModel.exam_session_id == exam.id,
            ExamAnswerModel.question_id == a.question_id,
        ).first()
        if not ans:
            # Placeholder row might have been deleted by an admin set update.
            # Recreate it so the user's submission is still recorded.
            ans = ExamAnswerModel(
                exam_session_id=exam.id,
                question_id=a.question_id,
            )
            db.add(ans)
        q = question_map.get(a.question_id)
        qtype = getattr(q, 'question_type', 'mcq') or 'mcq'
        # For MCQ/MULTI, evaluate correctness; for essay, store text but don't count towards score
        if qtype == 'mcq':
            objective_total += 1
            is_correct = (a.selected_answer or "").upper() == (q.correct_answer or "").upper()
        elif qtype == 'multi':
            objective_total += 1
            # Normalize sets of letters
            sel = set([(x or '').strip().upper() for x in (a.selected_answer or '').split(',') if x.strip()])
            cor = set([(x or '').strip().upper() for x in (q.correct_answer or '').split(',') if x.strip()])
            is_correct = (len(cor) > 0) and (sel == cor)
        else:
            is_correct = False
        ans.selected_answer = (a.selected_answer or None)
        ans.is_correct = is_correct
        if is_correct:
            correct += 1
        payload = {
            "question_id": q.id,
            "question_text": q.question_text,
            "selected_answer": a.selected_answer,
            "correct_answer": q.correct_answer,
            "is_correct": is_correct,
            "explanation": q.explanation,
            "selected_detail": _option_value(q, a.selected_answer) if qtype == 'mcq' else (a.selected_answer or ''),
            "correct_detail": _option_value(q, q.correct_answer) if qtype == 'mcq' else '',
            "question_type": qtype,
        }
        if qtype == 'multi':
            # Provide arrays of letter->detail for UI if needed
            sel_letters = [x for x in (a.selected_answer or '').split(',') if x.strip()]
            cor_letters = [x for x in (q.correct_answer or '').split(',') if x.strip()]
            payload["selected_multi"] = sel_letters
            payload["correct_multi"] = cor_letters
        elif qtype == 'essay':
            essay_ids.append(ans.id)
        answers_detail.append(payload)

    # finalize exam
    exam.correct_answers = correct
    # Score considers objective questions (mcq + multi)
    exam.score_percentage = (correct / max(1, objective_total)) * 100.0
    exam.is_completed = True
    # Use database time to match started_at (server_default=func.now())
    exam.completed_at = func.now()
    exam.time_taken_minutes = submission.time_taken_minutes

    db.commit()
    db.refresh(exam)

    # Compute essay grading summary (average of graded essays only)
    essay_count = len(essay_ids)
    essay_graded_count = 0
    essay_avg_score = None
    if essay_ids:
        grades = db.query(EssayGradeModel).filter(EssayGradeModel.exam_answer_id.in_(essay_ids)).all()
        scores = [g.score for g in grades if g and g.score is not None]
        essay_graded_count = len(scores)
        if scores:
            essay_avg_score = float(sum(scores)) / len(scores)
        # attach per-answer grade to payloads
        gmap = { g.exam_answer_id: g for g in grades }
        for p in answers_detail:
            # We need to locate the corresponding answer id; rebuild map from DB
            if p.get('question_type') == 'essay':
                # find the answer row for this question in this session
                ans = db.query(ExamAnswerModel).filter(ExamAnswerModel.exam_session_id == exam.id, ExamAnswerModel.question_id == p['question_id']).first()
                if ans:
                    g = gmap.get(ans.id)
                    if g:
                        p['essay_grade'] = { 'score': g.score, 'status': g.status, 'notes': g.notes }

    return ExamResult(
        exam_session_id=exam.id,
        total_questions=objective_total or 0,
        correct_answers=exam.correct_answers,
        score_percentage=exam.score_percentage,
        time_taken_minutes=exam.time_taken_minutes or 0.0,
        answers=answers_detail,
        essay_count=essay_count or 0,
        essay_graded_count=essay_graded_count or 0,
        essay_avg_score=essay_avg_score if essay_avg_score is not None else 0.0,
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
    # Preserve the original order (creation order matches the order from /start)
    answers_db = db.query(ExamAnswerModel).filter(ExamAnswerModel.exam_session_id == exam.id).order_by(ExamAnswerModel.id.asc()).all()
    qids = [a.question_id for a in answers_db]
    questions = { q.id: q for q in db.query(QuestionModel).filter(QuestionModel.id.in_(qids)).all() }
    answers_detail = []
    objective_total = 0
    essay_answer_ids = []
    for a in answers_db:
        q = questions.get(a.question_id)
        if not q:
            continue
        qtype = getattr(q, 'question_type', 'mcq') or 'mcq'
        if qtype in ('mcq','multi'):
            objective_total += 1
        payload = {
            "question_id": q.id,
            "question_text": q.question_text,
            "selected_answer": a.selected_answer,
            "correct_answer": q.correct_answer,
            "is_correct": a.is_correct or False,
            "explanation": q.explanation,
            "selected_detail": _option_value(q, a.selected_answer) if qtype == 'mcq' else (a.selected_answer or ''),
            "correct_detail": _option_value(q, q.correct_answer) if qtype == 'mcq' else '',
            "question_type": qtype,
        }
        if qtype == 'multi':
            sel_letters = [x for x in (a.selected_answer or '').split(',') if x.strip()]
            cor_letters = [x for x in (q.correct_answer or '').split(',') if x.strip()]
            payload["selected_multi"] = sel_letters
            payload["correct_multi"] = cor_letters
        elif qtype == 'essay':
            essay_answer_ids.append(a.id)
        answers_detail.append(payload)

    # essay summary
    essay_count = len(essay_answer_ids)
    essay_graded_count = 0
    essay_avg_score = None
    if essay_answer_ids:
        grades = db.query(EssayGradeModel).filter(EssayGradeModel.exam_answer_id.in_(essay_answer_ids)).all()
        scores = [g.score for g in grades if g and g.score is not None]
        essay_graded_count = len(scores)
        if scores:
            essay_avg_score = float(sum(scores)) / len(scores)
        gmap = { g.exam_answer_id: g for g in grades }
        for p in answers_detail:
            if p.get('question_type') == 'essay':
                # locate answer
                ans = next((x for x in answers_db if x.question_id == p['question_id']), None)
                if ans:
                    g = gmap.get(ans.id)
                    if g:
                        p['essay_grade'] = { 'score': g.score, 'status': g.status, 'notes': g.notes }

    return ExamResult(
        exam_session_id=exam.id,
        total_questions=objective_total or 0,
        correct_answers=exam.correct_answers or 0,
        score_percentage=exam.score_percentage or 0.0,
        time_taken_minutes=exam.time_taken_minutes or 0.0,
        answers=answers_detail,
        essay_count=essay_count or 0,
        essay_graded_count=essay_graded_count or 0,
        essay_avg_score=essay_avg_score if essay_avg_score is not None else 0.0,
    )
