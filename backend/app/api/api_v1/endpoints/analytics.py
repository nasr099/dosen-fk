from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy import case
from typing import Optional, List
from datetime import datetime, timedelta
import io, csv

from app.api.deps import get_current_admin_user
from app.db.base import get_db
from app.db.models import (
    ExamSession as ExamSessionModel,
    ExamAnswer as ExamAnswerModel,
    Question as QuestionModel,
    QuestionSet as QuestionSetModel,
    User as UserModel,
    EssayGrade as EssayGradeModel,
)

router = APIRouter()

@router.get("/sessions")
def analytics_sessions(
    q: Optional[str] = None,
    set_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin_user),
):
    base = (
        db.query(
            ExamSessionModel.id.label("session_id"),
            UserModel.id.label("user_id"),
            UserModel.email.label("user_email"),
            QuestionSetModel.id.label("set_id"),
            QuestionSetModel.title.label("set_title"),
            ExamSessionModel.score_percentage.label("objective_score"),
            ExamSessionModel.correct_answers.label("objective_correct"),
            ExamSessionModel.total_questions.label("objective_total"),
            ExamSessionModel.started_at,
            ExamSessionModel.completed_at,
        )
        .join(UserModel, ExamSessionModel.user_id == UserModel.id)
        .outerjoin(QuestionSetModel, ExamSessionModel.question_set_id == QuestionSetModel.id)
        .filter(ExamSessionModel.is_completed == True)
    )
    if set_id:
        base = base.filter(ExamSessionModel.question_set_id == set_id)
    if q:
        like = f"%{q.strip()}%"
        base = base.filter(UserModel.email.ilike(like))
    # Date range on completed_at (inclusive)
    def parse_date(s):
        try:
            return datetime.fromisoformat(s) if s else None
        except Exception:
            return None
    sd = parse_date(start_date)
    ed = parse_date(end_date)
    if sd:
        base = base.filter(ExamSessionModel.completed_at >= sd)
    if ed:
        # add one day if date w/o time to be inclusive
        end_dt = ed
        if len((end_date or "").strip()) <= 10:
            end_dt = ed + timedelta(days=1)
        base = base.filter(ExamSessionModel.completed_at < end_dt)

    base = base.order_by(ExamSessionModel.completed_at.desc().nullslast())

    # Pagination
    total = base.count()
    rows = base.offset((page - 1) * page_size).limit(page_size).all()

    session_ids = [r.session_id for r in rows]

    # Essay stats grouped by session
    essay_stats = {}
    if session_ids:
        agg = (
            db.query(ExamAnswerModel.exam_session_id.label("sid"), func.count(EssayGradeModel.id), func.avg(EssayGradeModel.score))
            .join(EssayGradeModel, EssayGradeModel.exam_answer_id == ExamAnswerModel.id)
            .filter(ExamAnswerModel.exam_session_id.in_(session_ids))
            .group_by(ExamAnswerModel.exam_session_id)
            .all()
        )
        for sid, cnt, avgscore in agg:
            essay_stats[sid] = {"essay_graded_count": int(cnt or 0), "essay_avg_score": float(avgscore or 0.0)}

    items = []
    for r in rows:
        est = essay_stats.get(r.session_id, {"essay_graded_count": 0, "essay_avg_score": 0.0})
        items.append({
            "session_id": r.session_id,
            "user_email": r.user_email,
            "set_id": r.set_id,
            "set_title": r.set_title,
            "objective_score": float(r.objective_score or 0.0),
            "objective_correct": int(r.objective_correct or 0),
            "objective_total": int(r.objective_total or 0),
            "essay_avg_score": est["essay_avg_score"],
            "essay_graded_count": est["essay_graded_count"],
            "started_at": r.started_at,
            "completed_at": r.completed_at,
        })

    return {"total": total, "items": items}

@router.get("/sessions/export")
def analytics_sessions_export(
    q: Optional[str] = None,
    set_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin_user),
):
    # Reuse the same query but without pagination
    base = (
        db.query(
            ExamSessionModel.id.label("session_id"),
            UserModel.email.label("user_email"),
            QuestionSetModel.title.label("set_title"),
            ExamSessionModel.score_percentage.label("objective_score"),
            ExamSessionModel.correct_answers.label("objective_correct"),
            ExamSessionModel.total_questions.label("objective_total"),
            ExamSessionModel.started_at,
            ExamSessionModel.completed_at,
        )
        .join(UserModel, ExamSessionModel.user_id == UserModel.id)
        .outerjoin(QuestionSetModel, ExamSessionModel.question_set_id == QuestionSetModel.id)
        .filter(ExamSessionModel.is_completed == True)
    )
    if set_id:
        base = base.filter(ExamSessionModel.question_set_id == set_id)
    if q:
        like = f"%{q.strip()}%"
        base = base.filter(UserModel.email.ilike(like))
    def parse_date(s):
        try:
            return datetime.fromisoformat(s) if s else None
        except Exception:
            return None
    sd = parse_date(start_date)
    ed = parse_date(end_date)
    if sd:
        base = base.filter(ExamSessionModel.completed_at >= sd)
    if ed:
        end_dt = ed
        if len((end_date or "").strip()) <= 10:
            end_dt = ed + timedelta(days=1)
        base = base.filter(ExamSessionModel.completed_at < end_dt)
    base = base.order_by(ExamSessionModel.completed_at.desc().nullslast())
    rows = base.all()

    session_ids = [r.session_id for r in rows]
    essay_stats = {}
    if session_ids:
        agg = (
            db.query(ExamAnswerModel.exam_session_id.label("sid"), func.count(EssayGradeModel.id), func.avg(EssayGradeModel.score))
            .join(EssayGradeModel, EssayGradeModel.exam_answer_id == ExamAnswerModel.id)
            .filter(ExamAnswerModel.exam_session_id.in_(session_ids))
            .group_by(ExamAnswerModel.exam_session_id)
            .all()
        )
        for sid, cnt, avgscore in agg:
            essay_stats[sid] = {"essay_graded_count": int(cnt or 0), "essay_avg_score": float(avgscore or 0.0)}

    # Build CSV
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(["Completed At","User","Set","Objective %","Correct","Total","Essay Avg %","Essay Graded","Session ID"]) 
    for r in rows:
        est = essay_stats.get(r.session_id, {"essay_graded_count": 0, "essay_avg_score": 0.0})
        w.writerow([
            str(r.completed_at or ""),
            r.user_email or "",
            r.set_title or "",
            f"{float(r.objective_score or 0.0):.2f}",
            int(r.objective_correct or 0),
            int(r.objective_total or 0),
            f"{est['essay_avg_score']:.2f}",
            int(est['essay_graded_count'] or 0),
            int(r.session_id),
        ])
    output.seek(0)
    filename = "analytics_sessions.csv"
    headers = {
        "Content-Disposition": f"attachment; filename={filename}",
        "Content-Type": "text/csv; charset=utf-8",
    }
    return StreamingResponse(iter([output.getvalue()]), headers=headers, media_type="text/csv")


@router.get("/sets")
def analytics_sets(
    db: Session = Depends(get_db),
    _=Depends(get_current_admin_user),
):
    # Objective summary per set
    obj_rows = (
        db.query(
            QuestionSetModel.id.label("set_id"),
            QuestionSetModel.title.label("set_title"),
            func.count(ExamSessionModel.id).label("sessions_completed"),
            func.avg(ExamSessionModel.score_percentage).label("avg_objective_score"),
        )
        .outerjoin(ExamSessionModel, ExamSessionModel.question_set_id == QuestionSetModel.id)
        .filter((ExamSessionModel.is_completed == True) | (ExamSessionModel.id.is_(None)))
        .group_by(QuestionSetModel.id, QuestionSetModel.title)
        .order_by(QuestionSetModel.title.asc())
        .all()
    )

    # Essay summary per set (average of all essay grades across sessions of the set)
    essay_rows = (
        db.query(
            QuestionSetModel.id.label("set_id"),
            func.count(EssayGradeModel.id).label("essay_graded_count"),
            func.avg(EssayGradeModel.score).label("avg_essay_score"),
        )
        .join(QuestionModel, QuestionModel.question_set_id == QuestionSetModel.id)
        .join(ExamAnswerModel, ExamAnswerModel.question_id == QuestionModel.id)
        .join(EssayGradeModel, EssayGradeModel.exam_answer_id == ExamAnswerModel.id)
        .group_by(QuestionSetModel.id)
        .all()
    )
    essay_map = {r.set_id: {"essay_graded_count": int(r.essay_graded_count or 0), "avg_essay_score": float(r.avg_essay_score or 0.0)} for r in essay_rows}

    items = []
    for r in obj_rows:
        em = essay_map.get(r.set_id, {"essay_graded_count": 0, "avg_essay_score": 0.0})
        items.append({
            "set_id": r.set_id,
            "set_title": r.set_title,
            "sessions_completed": int(r.sessions_completed or 0),
            "avg_objective_score": float(r.avg_objective_score or 0.0),
            "avg_essay_score": em["avg_essay_score"],
            "essay_graded_count": em["essay_graded_count"],
        })

    return {"items": items}


@router.get("/trends")
def analytics_trends(
    bucket: str = Query("day", regex="^(day|week)$"),
    set_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin_user),
):
    # Build base completed sessions
    base = db.query(
        ExamSessionModel.id.label("sid"),
        ExamSessionModel.completed_at.label("completed_at"),
        ExamSessionModel.score_percentage.label("objective"),
    ).filter(ExamSessionModel.is_completed == True)
    if set_id:
        base = base.filter(ExamSessionModel.question_set_id == set_id)
    def parse_date(s):
        try: return datetime.fromisoformat(s) if s else None
        except Exception: return None
    sd = parse_date(start_date); ed = parse_date(end_date)
    if sd: base = base.filter(ExamSessionModel.completed_at >= sd)
    if ed:
        end_dt = ed if not (end_date and len(end_date.strip())<=10) else ed + timedelta(days=1)
        base = base.filter(ExamSessionModel.completed_at < end_dt)
    sessions = base.all()
    sids = [r.sid for r in sessions]
    # Essay avg per session
    eavg = {}
    if sids:
        agg = (
            db.query(ExamAnswerModel.exam_session_id.label("sid"), func.avg(EssayGradeModel.score))
            .join(EssayGradeModel, EssayGradeModel.exam_answer_id == ExamAnswerModel.id)
            .filter(ExamAnswerModel.exam_session_id.in_(sids))
            .group_by(ExamAnswerModel.exam_session_id)
            .all()
        )
        eavg = { sid: float(avg or 0.0) for sid, avg in agg }
    # Bucketize
    def bucket_key(dt: datetime):
        if bucket == 'week':
            iso_year, iso_week, _ = (dt or datetime.utcnow()).isocalendar()
            return f"{iso_year}-W{iso_week:02d}"
        return (dt or datetime.utcnow()).strftime("%Y-%m-%d")
    data = {}
    for r in sessions:
        k = bucket_key(r.completed_at)
        d = data.setdefault(k, {"objective_sum":0.0, "objective_cnt":0, "essay_sum":0.0, "essay_cnt":0})
        d["objective_sum"] += float(r.objective or 0.0)
        d["objective_cnt"] += 1
        if r.sid in eavg:
            d["essay_sum"] += eavg[r.sid]
            d["essay_cnt"] += 1
    items = []
    for k in sorted(data.keys()):
        d = data[k]
        items.append({
            "bucket": k,
            "objective_avg": (d["objective_sum"]/max(1,d["objective_cnt"])) ,
            "essay_avg": (d["essay_sum"]/max(1,d["essay_cnt"])) ,
            "count": d["objective_cnt"],
        })
    return {"items": items}


@router.get("/distributions")
def analytics_distributions(
    set_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin_user),
):
    # Helper to parse dates
    def parse_date(s):
        try: return datetime.fromisoformat(s) if s else None
        except Exception: return None
    sd = parse_date(start_date); ed = parse_date(end_date)
    # Objective scores
    q = db.query(ExamSessionModel.score_percentage, ExamSessionModel.completed_at).filter(ExamSessionModel.is_completed==True)
    if set_id: q = q.filter(ExamSessionModel.question_set_id == set_id)
    if sd: q = q.filter(ExamSessionModel.completed_at >= sd)
    if ed:
        end_dt = ed if not (end_date and len(end_date.strip())<=10) else ed + timedelta(days=1)
        q = q.filter(ExamSessionModel.completed_at < end_dt)
    obj_scores = [float(x[0] or 0.0) for x in q.all()]
    # Essay session averages
    eavg = []
    sids = [sid for (sid,) in db.query(ExamSessionModel.id).filter(ExamSessionModel.is_completed==True).all()]
    if sids:
        e = (
            db.query(ExamAnswerModel.exam_session_id, func.avg(EssayGradeModel.score))
            .join(EssayGradeModel, EssayGradeModel.exam_answer_id == ExamAnswerModel.id)
            .filter(ExamAnswerModel.exam_session_id.in_(sids))
            .group_by(ExamAnswerModel.exam_session_id)
            .all()
        )
        eavg = [float(a or 0.0) for _, a in e]
    def hist(arr):
        bins = [0]*10
        for v in arr:
            idx = int(max(0, min(9, v // 10)))
            bins[idx] += 1
        return bins
    return {"objective": hist(obj_scores), "essay": hist(eavg)}


@router.get("/insights/top-missed")
def insights_top_missed(
    limit: int = 20,
    set_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin_user),
):
    # Count incorrect answers for mcq/multi per question
    # Parse dates
    def parse_date(s):
        try: return datetime.fromisoformat(s) if s else None
        except Exception: return None
    sd = parse_date(start_date); ed = parse_date(end_date)

    q = (
        db.query(
            QuestionModel.id.label("question_id"),
            QuestionModel.question_text,
            QuestionSetModel.title.label("set_title"),
            func.sum(case((ExamAnswerModel.is_correct == False, 1), else_=0)).label("incorrect_count"),
            func.count(ExamAnswerModel.id).label("attempts"),
        )
        .join(QuestionModel, QuestionModel.id == ExamAnswerModel.question_id)
        .outerjoin(QuestionSetModel, QuestionModel.question_set_id == QuestionSetModel.id)
        .join(ExamSessionModel, ExamSessionModel.id == ExamAnswerModel.exam_session_id)
        .filter(QuestionModel.question_type.in_(["mcq","multi"]))
        .group_by(QuestionModel.id, QuestionModel.question_text, QuestionSetModel.title)
    )
    if set_id:
        q = q.filter(QuestionModel.question_set_id == set_id)
    if sd:
        q = q.filter(ExamSessionModel.completed_at >= sd)
    if ed:
        end_dt = ed if not (end_date and len(end_date.strip())<=10) else ed + timedelta(days=1)
        q = q.filter(ExamSessionModel.completed_at < end_dt)
    rows = q.order_by(func.sum(case((ExamAnswerModel.is_correct == False, 1), else_=0)).desc()).limit(limit).all()
    items = []
    for r in rows:
        items.append({
            "question_id": r.question_id,
            "question_text": r.question_text,
            "set_title": r.set_title,
            "incorrect_count": int(r.incorrect_count or 0),
            "attempts": int(r.attempts or 0),
        })
    return {"items": items}


@router.get("/insights/essay-questions")
def insights_essay_questions(
    limit: int = 20,
    set_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin_user),
):
    def parse_date(s):
        try: return datetime.fromisoformat(s) if s else None
        except Exception: return None
    sd = parse_date(start_date); ed = parse_date(end_date)
    q = (
        db.query(
            QuestionModel.id.label("question_id"),
            QuestionModel.question_text,
            QuestionSetModel.title.label("set_title"),
            func.count(EssayGradeModel.id).label("graded"),
            func.avg(EssayGradeModel.score).label("avg_score"),
        )
        .join(ExamAnswerModel, ExamAnswerModel.question_id == QuestionModel.id)
        .join(EssayGradeModel, EssayGradeModel.exam_answer_id == ExamAnswerModel.id)
        .outerjoin(QuestionSetModel, QuestionModel.question_set_id == QuestionSetModel.id)
        .join(ExamSessionModel, ExamSessionModel.id == ExamAnswerModel.exam_session_id)
        .filter((QuestionModel.question_type == 'essay'))
        .group_by(QuestionModel.id, QuestionModel.question_text, QuestionSetModel.title)
    )
    if set_id:
        q = q.filter(QuestionModel.question_set_id == set_id)
    if sd:
        q = q.filter(ExamSessionModel.completed_at >= sd)
    if ed:
        end_dt = ed if not (end_date and len(end_date.strip())<=10) else ed + timedelta(days=1)
        q = q.filter(ExamSessionModel.completed_at < end_dt)
    rows = q.order_by(func.avg(EssayGradeModel.score).asc()).limit(limit).all()
    return {"items": [
        {"question_id": r.question_id, "question_text": r.question_text, "set_title": r.set_title, "graded": int(r.graded or 0), "avg_score": float(r.avg_score or 0.0)}
        for r in rows
    ]}


@router.get("/progress")
def analytics_progress(
    set_id: Optional[int] = None,
    limit: int = 50,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin_user),
):
    # For each user+set, compare earliest vs latest completed objective score
    # Parse dates
    def parse_date(s):
        try: return datetime.fromisoformat(s) if s else None
        except Exception: return None
    sd = parse_date(start_date); ed = parse_date(end_date)

    sub = (
        db.query(
            ExamSessionModel.user_id.label("uid"),
            ExamSessionModel.question_set_id.label("sid"),
            func.min(ExamSessionModel.completed_at).label("first"),
            func.max(ExamSessionModel.completed_at).label("last"),
        )
        .filter(ExamSessionModel.is_completed == True)
        .filter(*( [ExamSessionModel.completed_at >= sd] if sd else [] ))
        .filter(*( [ExamSessionModel.completed_at < (ed + timedelta(days=1) if (ed and (not end_date or len(end_date.strip())<=10)) else ed)] if ed else [] ))
        .group_by(ExamSessionModel.user_id, ExamSessionModel.question_set_id)
        .subquery()
    )
    q = (
        db.query(
            UserModel.email,
            QuestionSetModel.title,
            ExamSessionModel.score_percentage,
            ExamSessionModel.completed_at,
            sub.c.first,
            sub.c.last,
        )
        .join(sub, (sub.c.uid == ExamSessionModel.user_id) & (sub.c.sid == ExamSessionModel.question_set_id))
        .join(UserModel, UserModel.id == ExamSessionModel.user_id)
        .outerjoin(QuestionSetModel, QuestionSetModel.id == ExamSessionModel.question_set_id)
        .filter(ExamSessionModel.is_completed == True)
    )
    if set_id:
        q = q.filter(ExamSessionModel.question_set_id == set_id)
    # Apply same date filters to the detailed rows as well
    if sd:
        q = q.filter(ExamSessionModel.completed_at >= sd)
    if ed:
        end_dt = ed if not (end_date and len(end_date.strip())<=10) else ed + timedelta(days=1)
        q = q.filter(ExamSessionModel.completed_at < end_dt)
    rows = q.all()
    # Aggregate per user+set
    data = {}
    for r in rows:
        key = (r.email, r.title)
        d = data.setdefault(key, {"first_score": None, "last_score": None, "first_at": r.first, "last_at": r.last})
        if r.completed_at == r.first:
            d["first_score"] = float(r.score_percentage or 0.0)
        if r.completed_at == r.last:
            d["last_score"] = float(r.score_percentage or 0.0)
    items = []
    for (email, title), v in list(data.items())[:limit]:
        delta = (v["last_score"] or 0.0) - (v["first_score"] or 0.0)
        items.append({
            "user_email": email,
            "set_title": title,
            "first_score": v["first_score"] or 0.0,
            "last_score": v["last_score"] or 0.0,
            "delta": delta,
            "first_at": v["first_at"],
            "last_at": v["last_at"],
        })
    # Sort by improvement desc
    items.sort(key=lambda x: x["delta"], reverse=True)
    return {"items": items[:limit]}
