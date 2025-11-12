from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional
from datetime import datetime, timedelta, timezone

from app.api.deps import get_db, get_current_user, get_current_staff_user
from app.db.models import (
    Tryout as TryoutModel,
    TryoutSet as TryoutSetModel,
    TryoutSession as TryoutSessionModel,
    TryoutSetSession as TryoutSetSessionModel,
    TryoutAnswer as TryoutAnswerModel,
    TryoutMeta as TryoutMetaModel,
    TryoutCategory as TryoutCategoryModel,
    QuestionSet as QuestionSetModel,
    Question as QuestionModel,
    User as UserModel,
)
from app.schemas.tryout import Tryout as TryoutSchema, TryoutCreate, TryoutUpdate, TryoutCurrentPhase, CurrentSetMeta, TryoutResult, TryoutResultSet

router = APIRouter()

# ---------- Categories ----------
@router.get('/categories', response_model=List[str])
def list_tryout_categories(db: Session = Depends(get_db)):
    rows = db.query(TryoutCategoryModel).order_by(TryoutCategoryModel.name.asc()).all()
    return [r.name for r in rows]

@router.post('/categories', response_model=str)
def create_tryout_category(name: str, db: Session = Depends(get_db), staff=Depends(get_current_staff_user)):
    name = (name or '').strip()
    if not name:
        raise HTTPException(status_code=400, detail='Name is required')
    exists = db.query(TryoutCategoryModel).filter(TryoutCategoryModel.name.ilike(name)).first()
    if exists:
        return exists.name
    row = TryoutCategoryModel(name=name)
    db.add(row); db.commit(); db.refresh(row)
    return row.name

# List categories with ids for management UI
@router.get('/categories/all')
def list_tryout_categories_full(db: Session = Depends(get_db), _=Depends(get_current_staff_user)):
    rows = db.query(TryoutCategoryModel).order_by(TryoutCategoryModel.name.asc()).all()
    return [ { 'id': r.id, 'name': r.name } for r in rows ]

# Update category name
@router.put('/categories/{cat_id}', response_model=str)
def update_tryout_category(cat_id: int, name: str, db: Session = Depends(get_db), _=Depends(get_current_staff_user)):
    name = (name or '').strip()
    if not name:
        raise HTTPException(status_code=400, detail='Name is required')
    row = db.query(TryoutCategoryModel).filter(TryoutCategoryModel.id == cat_id).first()
    if not row:
        raise HTTPException(status_code=404, detail='Category not found')
    # prevent duplicate
    exists = db.query(TryoutCategoryModel).filter(TryoutCategoryModel.name.ilike(name), TryoutCategoryModel.id != cat_id).first()
    if exists:
        raise HTTPException(status_code=409, detail='Category name already exists')
    row.name = name
    db.commit(); db.refresh(row)
    return row.name

# Delete category
@router.delete('/categories/{cat_id}')
def delete_tryout_category(cat_id: int, db: Session = Depends(get_db), _=Depends(get_current_staff_user)):
    row = db.query(TryoutCategoryModel).filter(TryoutCategoryModel.id == cat_id).first()
    if not row:
        raise HTTPException(status_code=404, detail='Category not found')
    # Reassign any tryouts using this category to 'Uncategorized'
    name = row.name
    if name:
        metas = db.query(TryoutMetaModel).filter(TryoutMetaModel.category == name).all()
        for m in metas:
            m.category = 'Uncategorized'
    db.delete(row)
    db.commit()
    return { 'ok': True }

# ---- Admin CRUD ----
@router.post('/', response_model=TryoutSchema)
def create_tryout(payload: TryoutCreate, db: Session = Depends(get_db), staff=Depends(get_current_staff_user)):
    t = TryoutModel(title=payload.title, description=payload.description, is_active=payload.is_active, created_by=getattr(staff, 'id', None))
    db.add(t)
    db.commit(); db.refresh(t)
    # Save meta category (separate from Questions category)
    if getattr(payload, 'category', None) is not None:
        cat = (payload.category or '').strip() or 'Uncategorized'
        m = TryoutMetaModel(tryout_id=t.id, category=cat)
        db.add(m); db.commit()
    # create sets
    for s in sorted(payload.sets or [], key=lambda x: x.order_index):
        # ensure referenced set is allowed for tryout
        qs = db.query(QuestionSetModel).filter(QuestionSetModel.id == s.question_set_id, QuestionSetModel.allow_in_tryout == True).first()
        if not qs:
            raise HTTPException(status_code=400, detail=f"question_set_id {s.question_set_id} is not allowed for tryouts")
        db.add(TryoutSetModel(tryout_id=t.id, order_index=s.order_index, question_set_id=s.question_set_id, duration_minutes=s.duration_minutes, intermission_text=s.intermission_text))
    db.commit(); db.refresh(t)
    return t

# ---- Admin Analytics: Tryout Sessions ----
@router.get('/analytics/tryout-sessions')
def analytics_tryout_sessions(
    tryout_id: int,
    q: str = "",
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    _=Depends(get_current_staff_user),
):
    page = max(1, int(page or 1)); page_size = max(1, min(int(page_size or 20), 100))
    # total sets for progress column
    sets_total = db.query(TryoutSetModel).filter(TryoutSetModel.tryout_id == tryout_id).count()
    base = (
        db.query(
            TryoutSessionModel.id.label('session_id'),
            UserModel.email.label('user_email'),
            TryoutSessionModel.status,
            TryoutSessionModel.started_at,
            TryoutSessionModel.finished_at,
        )
        .join(UserModel, UserModel.id == TryoutSessionModel.user_id)
        .filter(TryoutSessionModel.tryout_id == tryout_id)
        .order_by(TryoutSessionModel.started_at.desc().nullslast())
    )
    if q:
        like = f"%{q.strip()}%"; base = base.filter(UserModel.email.ilike(like))
    total = base.count()
    rows = base.offset((page-1)*page_size).limit(page_size).all()
    sids = [r.session_id for r in rows]
    # finished set sessions per session id
    finished_map = {}
    if sids:
        agg = (
            db.query(TryoutSetSessionModel.tryout_session_id, func.count(TryoutSetSessionModel.id))
            .filter(TryoutSetSessionModel.tryout_session_id.in_(sids), TryoutSetSessionModel.phase == 'finished')
            .group_by(TryoutSetSessionModel.tryout_session_id)
            .all()
        )
        finished_map = { sid: int(cnt or 0) for sid, cnt in agg }
    items = []
    for r in rows:
        items.append({
            'session_id': r.session_id,
            'user_email': r.user_email,
            'status': r.status,
            'started_at': r.started_at,
            'finished_at': r.finished_at,
            'sets_finished': int(finished_map.get(r.session_id) or 0),
            'sets_total': int(sets_total or 0),
        })
    return { 'total': total, 'items': items, 'sets_total': int(sets_total or 0) }

@router.delete('/{tryout_id}')
def delete_tryout(tryout_id: int, db: Session = Depends(get_db), _=Depends(get_current_staff_user)):
    t = db.query(TryoutModel).filter(TryoutModel.id == tryout_id).first()
    if not t:
        raise HTTPException(status_code=404, detail='Tryout not found')
    # Clean up related data
    from app.db.models import TryoutSetSession as TSSModel, EssayGrade as EssayGradeModel
    # Sets
    set_ids = [row.id for row in db.query(TryoutSetModel.id).filter(TryoutSetModel.tryout_id == tryout_id).all()]
    # Set sessions
    tss_ids = []
    if set_ids:
        tss_ids = [row.id for row in db.query(TSSModel.id).filter(TSSModel.tryout_set_id.in_(set_ids)).all()]
    # Answers and grades
    if tss_ids:
        ans_ids = [row.id for row in db.query(TryoutAnswerModel.id).filter(TryoutAnswerModel.tryout_set_session_id.in_(tss_ids)).all()]
        if ans_ids:
            db.query(EssayGradeModel).filter(EssayGradeModel.tryout_answer_id.in_(ans_ids)).delete(synchronize_session=False)
            db.query(TryoutAnswerModel).filter(TryoutAnswerModel.id.in_(ans_ids)).delete(synchronize_session=False)
        db.query(TSSModel).filter(TSSModel.id.in_(tss_ids)).delete(synchronize_session=False)
    # Sessions
    db.query(TryoutSessionModel).filter(TryoutSessionModel.tryout_id == tryout_id).delete(synchronize_session=False)
    # Sets
    db.query(TryoutSetModel).filter(TryoutSetModel.tryout_id == tryout_id).delete(synchronize_session=False)
    # Meta
    db.query(TryoutMetaModel).filter(TryoutMetaModel.tryout_id == tryout_id).delete(synchronize_session=False)
    # Tryout
    db.delete(t)
    db.commit()
    return { 'ok': True }

@router.put('/{tryout_id}', response_model=TryoutSchema)
def update_tryout(tryout_id: int, payload: TryoutUpdate, db: Session = Depends(get_db), staff=Depends(get_current_staff_user)):
    t = db.query(TryoutModel).filter(TryoutModel.id == tryout_id).first()
    if not t: raise HTTPException(status_code=404, detail='Tryout not found')
    for k, v in payload.model_dump(exclude_unset=True, exclude={'sets'}).items():
        setattr(t, k, v)
    db.commit(); db.refresh(t)
    # Upsert meta category (default to 'Uncategorized' when empty)
    if 'category' in payload.model_dump(exclude_unset=True):
        cat = (payload.category or '').strip() or 'Uncategorized'
        m = db.query(TryoutMetaModel).filter(TryoutMetaModel.tryout_id == tryout_id).first()
        if not m:
            m = TryoutMetaModel(tryout_id=tryout_id, category=cat)
            db.add(m)
        else:
            m.category = cat
        db.commit()
    if payload.sets is not None:
        db.query(TryoutSetModel).filter(TryoutSetModel.tryout_id == tryout_id).delete(synchronize_session=False)
        db.commit()
        for s in sorted(payload.sets or [], key=lambda x: x.order_index):
            qs = db.query(QuestionSetModel).filter(QuestionSetModel.id == s.question_set_id, QuestionSetModel.allow_in_tryout == True).first()
            if not qs:
                raise HTTPException(status_code=400, detail=f"question_set_id {s.question_set_id} is not allowed for tryouts")
            db.add(TryoutSetModel(tryout_id=t.id, order_index=s.order_index, question_set_id=s.question_set_id, duration_minutes=s.duration_minutes, intermission_text=s.intermission_text))
        db.commit()
    return t

@router.get('/')
def list_tryouts(
    include_all: bool = False,
    paginated: bool = False,
    q: str = "",
    category: str = "",
    status: str = "active",  # active | inactive | all
    sort_by: str = "created_at",  # title | sets | duration | created_at
    sort_dir: str = "desc",  # asc | desc
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    # Base query
    base = db.query(TryoutModel)
    # status filter (default to active unless include_all with status=all)
    if status in ("active", "inactive"):
        want = (status == "active")
        base = base.filter(TryoutModel.is_active == want)
    elif not include_all:
        base = base.filter(TryoutModel.is_active == True)
    # search
    if q:
        like = f"%{q.strip()}%"
        base = base.filter(TryoutModel.title.ilike(like))
    # category filter via meta
    from sqlalchemy.orm import aliased
    TM = TryoutMetaModel
    if category:
        base = base.join(TM, TM.tryout_id == TryoutModel.id, isouter=True).filter(TM.category == category)

    # Sorting helpers via subqueries for sets and duration
    from app.db.models import TryoutSet as TS
    sets_count = db.query(TS.tryout_id, func.count(TS.id).label('cnt')).group_by(TS.tryout_id).subquery()
    duration_sum = db.query(TS.tryout_id, func.coalesce(func.sum(TS.duration_minutes), 0).label('mins')).group_by(TS.tryout_id).subquery()

    dir_desc = (sort_dir or 'desc').lower() == 'desc'
    if sort_by == 'title':
        base = base.order_by(getattr(TryoutModel.title, 'desc' if dir_desc else 'asc')())
    elif sort_by == 'sets':
        base = base.outerjoin(sets_count, sets_count.c.tryout_id == TryoutModel.id).order_by((sets_count.c.cnt.desc() if dir_desc else sets_count.c.cnt.asc()).nullslast())
    elif sort_by == 'duration':
        base = base.outerjoin(duration_sum, duration_sum.c.tryout_id == TryoutModel.id).order_by((duration_sum.c.mins.desc() if dir_desc else duration_sum.c.mins.asc()).nullslast())
    else:
        base = base.order_by(getattr(TryoutModel.created_at, 'desc' if dir_desc else 'asc')())

    if not paginated:
        rows = base.all()
        ids = [r.id for r in rows]
        # category map
        metas = {}
        if ids:
            for m in db.query(TryoutMetaModel).filter(TryoutMetaModel.tryout_id.in_(ids)).all():
                metas[m.tryout_id] = m.category
        # sets count and duration maps
        from app.db.models import TryoutSet as TS
        sc_map = { r.tryout_id: r.cnt for r in db.query(TS.tryout_id, func.count(TS.id).label('cnt')).filter(TS.tryout_id.in_(ids)).group_by(TS.tryout_id).all() }
        du_map = { r.tryout_id: int(r.mins or 0) for r in db.query(TS.tryout_id, func.coalesce(func.sum(TS.duration_minutes), 0).label('mins')).filter(TS.tryout_id.in_(ids)).group_by(TS.tryout_id).all() }
        out = []
        for r in rows:
            out.append({
                'id': r.id,
                'title': r.title,
                'description': r.description,
                'is_active': r.is_active,
                'created_at': r.created_at,
                'category': metas.get(r.id),
                'sets_count': int(sc_map.get(r.id) or 0),
                'duration_minutes': int(du_map.get(r.id) or 0),
            })
        return out
    # Paginated branch
    limit = max(1, min(int(limit or 20), 100))
    offset = max(0, int(offset or 0))
    total = base.count()
    rows = base.offset(offset).limit(limit).all()
    ids = [r.id for r in rows]
    metas = {}
    if ids:
        for m in db.query(TryoutMetaModel).filter(TryoutMetaModel.tryout_id.in_(ids)).all():
            metas[m.tryout_id] = m.category
    from app.db.models import TryoutSet as TS
    sc_map = { r.tryout_id: r.cnt for r in db.query(TS.tryout_id, func.count(TS.id).label('cnt')).filter(TS.tryout_id.in_(ids)).group_by(TS.tryout_id).all() }
    du_map = { r.tryout_id: int(r.mins or 0) for r in db.query(TS.tryout_id, func.coalesce(func.sum(TS.duration_minutes), 0).label('mins')).filter(TS.tryout_id.in_(ids)).group_by(TS.tryout_id).all() }
    items = []
    for r in rows:
        items.append({
            'id': r.id,
            'title': r.title,
            'description': r.description,
            'is_active': r.is_active,
            'created_at': r.created_at,
            'category': metas.get(r.id),
            'sets_count': int(sc_map.get(r.id) or 0),
            'duration_minutes': int(du_map.get(r.id) or 0),
        })
    return { 'items': items, 'total': total }

@router.get('/{tryout_id}', response_model=TryoutSchema)
def get_tryout(tryout_id: int, db: Session = Depends(get_db)):
    t = db.query(TryoutModel).filter(TryoutModel.id == tryout_id).first()
    if not t: raise HTTPException(status_code=404, detail='Tryout not found')
    m = db.query(TryoutMetaModel).filter(TryoutMetaModel.tryout_id == tryout_id).first()
    try:
        setattr(t, 'category', getattr(m, 'category', None))
    except Exception:
        pass
    return t

# ---- Student flow ----
@router.post('/{tryout_id}/start')
def start_tryout(
    tryout_id: int,
    request: Request,
    x_device_id: Optional[str] = Header(None, alias='X-Device-Id'),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # Enforce resume-only: if any unfinished session for this tryout exists for this user, reuse it
    existing = (
        db.query(TryoutSessionModel)
        .filter(
            TryoutSessionModel.user_id == user.id,
            TryoutSessionModel.tryout_id == tryout_id,
            TryoutSessionModel.status != 'finished',
        )
        .order_by(TryoutSessionModel.started_at.desc())
        .first()
    )
    if existing:
        # Check if there is an active set session for this tryout session
        active_tss = db.query(TryoutSetSessionModel).filter(
            TryoutSetSessionModel.tryout_session_id == existing.id,
            TryoutSetSessionModel.phase.in_(['intermission','running'])
        ).order_by(TryoutSetSessionModel.id.desc()).first()
        if not active_tss:
            # No active set -> mark as finished and allow new start
            try:
                existing.status = 'finished'; existing.finished_at = datetime.now(timezone.utc)
                db.commit()
            except Exception:
                db.rollback()
        else:
            # Validate referenced set still exists; otherwise close and create new
            ts_exists = db.query(TryoutSetModel).filter(TryoutSetModel.id == active_tss.tryout_set_id).first()
            if not ts_exists:
                try:
                    existing.status = 'finished'; existing.finished_at = datetime.now(timezone.utc)
                    db.commit()
                except Exception:
                    db.rollback()
            else:
        # If device is already bound and header mismatches, refuse creating/resuming on different device
                if getattr(existing, 'device_id', None):
                    if x_device_id and existing.device_id != x_device_id:
                        raise HTTPException(status_code=409, detail='Active tryout is locked to another device')
                else:
                    # Bind legacy existing session if header present
                    if x_device_id:
                        try:
                            existing.device_id = x_device_id
                            existing.user_agent = request.headers.get('user-agent')
                            existing.started_ip = request.client.host if request.client else None
                            db.commit()
                        except Exception:
                            db.rollback()
                return { 'tryout_session_id': existing.id }

    # create new session and first set session in running
    t = db.query(TryoutModel).filter(TryoutModel.id == tryout_id, TryoutModel.is_active == True).first()
    if not t: raise HTTPException(status_code=404, detail='Tryout not found')
    first = db.query(TryoutSetModel).filter(TryoutSetModel.tryout_id == tryout_id).order_by(TryoutSetModel.order_index.asc()).first()
    if not first: raise HTTPException(status_code=400, detail='Tryout has no sets')

    sess = TryoutSessionModel(tryout_id=tryout_id, user_id=user.id, status='running')
    # Save device binding on start if provided
    try:
        if x_device_id:
            setattr(sess, 'device_id', x_device_id)
        setattr(sess, 'user_agent', request.headers.get('user-agent'))
        setattr(sess, 'started_ip', request.client.host if request.client else None)
    except Exception:
        pass
    db.add(sess); db.commit(); db.refresh(sess)

    now = datetime.now(timezone.utc)
    run_end = now + timedelta(minutes=first.duration_minutes or 60)
    tss = TryoutSetSessionModel(
        tryout_session_id=sess.id,
        tryout_set_id=first.id,
        phase='running',
        intermission_start_at=None,
        intermission_end_at=None,
        run_start_at=now,
        run_end_at=run_end,
    )
    db.add(tss); db.commit()
    return { 'tryout_session_id': sess.id }

@router.get('/sessions/{session_id}/current', response_model=TryoutCurrentPhase)
def get_current_phase(
    session_id: int,
    request: Request,
    x_device_id: Optional[str] = Header(None, alias='X-Device-Id'),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    sess = db.query(TryoutSessionModel).filter(TryoutSessionModel.id == session_id, TryoutSessionModel.user_id == user.id).first()
    if not sess: raise HTTPException(status_code=404, detail='Session not found')
    # Device validation
    if getattr(sess, 'device_id', None):
        if x_device_id and sess.device_id != x_device_id:
            raise HTTPException(status_code=409, detail='Session is locked to another device')
    elif x_device_id:
        try:
            sess.device_id = x_device_id
            sess.user_agent = request.headers.get('user-agent')
            sess.started_ip = request.client.host if request.client else None
            db.commit()
        except Exception:
            db.rollback()
    # find current set session (last created)
    tss = db.query(TryoutSetSessionModel).filter(TryoutSetSessionModel.tryout_session_id == session_id).order_by(TryoutSetSessionModel.id.desc()).first()
    now = datetime.now(timezone.utc)
    if not tss:
        return TryoutCurrentPhase(tryout_session_id=sess.id, tss_id=0, order_index=0, phase='done', now=now)
    # resolve set meta
    ts = db.query(TryoutSetModel).filter(TryoutSetModel.id == tss.tryout_set_id).first()
    if not ts:
        # Referenced set was removed; treat session as done to avoid crash
        return TryoutCurrentPhase(tryout_session_id=sess.id, tss_id=getattr(tss,'id',0), order_index=0, phase='done', now=now)
    # If time has expired while in running phase, auto-finish this set on the server
    if tss.phase == 'running' and tss.run_end_at and now >= tss.run_end_at:
        try:
            # compute score and finish current set
            total = db.query(QuestionModel).filter(QuestionModel.question_set_id == ts.question_set_id).count()
            answered = db.query(TryoutAnswerModel).filter(TryoutAnswerModel.tryout_set_session_id == tss.id).count()
            correct = db.query(TryoutAnswerModel).filter(
                TryoutAnswerModel.tryout_set_session_id == tss.id,
                TryoutAnswerModel.is_correct == True
            ).count()
            pct = (correct / total * 100.0) if total else 0.0
            tss.answered_count = answered
            tss.correct_count = correct
            tss.score_percentage = pct
            tss.phase = 'finished'
            db.commit()
            # move to next set or close whole tryout
            next_set = db.query(TryoutSetModel).filter(
                TryoutSetModel.tryout_id == ts.tryout_id,
                TryoutSetModel.order_index > ts.order_index
            ).order_by(TryoutSetModel.order_index.asc()).first()
            if next_set:
                inter_end = now + timedelta(seconds=60)
                next_tss = TryoutSetSessionModel(
                    tryout_session_id=sess.id,
                    tryout_set_id=next_set.id,
                    phase='intermission',
                    intermission_start_at=now,
                    intermission_end_at=inter_end,
                )
                db.add(next_tss)
                db.commit()
                tss = next_tss
                ts = next_set
            else:
                sess.status = 'finished'; sess.finished_at = now
                db.commit()
                return TryoutCurrentPhase(tryout_session_id=sess.id, tss_id=tss.id, order_index=0, phase='done', now=now)
        except Exception:
            db.rollback()
    # enrich with question set title and description
    qs = db.query(QuestionSetModel).filter(QuestionSetModel.id==ts.question_set_id).first()
    set_meta = CurrentSetMeta(
        id=ts.id,
        order_index=ts.order_index,
        title=(qs.title if qs and qs.title else f"Set {ts.order_index}"),
        duration_minutes=ts.duration_minutes,
        question_set_id=ts.question_set_id,
        intermission_text=ts.intermission_text,
        description=(qs.description if qs else None),
    )
    return TryoutCurrentPhase(tryout_session_id=sess.id, tss_id=tss.id, order_index=ts.order_index, phase=tss.phase, now=now, intermission_end_at=tss.intermission_end_at, run_end_at=tss.run_end_at, set=set_meta)

@router.post('/set-sessions/{tss_id}/begin-run')
def begin_run(
    tss_id: int,
    request: Request,
    x_device_id: Optional[str] = Header(None, alias='X-Device-Id'),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    tss = db.query(TryoutSetSessionModel).filter(TryoutSetSessionModel.id == tss_id).first()
    if not tss: raise HTTPException(status_code=404, detail='Set session not found')
    sess = db.query(TryoutSessionModel).filter(TryoutSessionModel.id == tss.tryout_session_id, TryoutSessionModel.user_id == user.id).first()
    if not sess: raise HTTPException(status_code=403, detail='Forbidden')
    if getattr(sess, 'device_id', None):
        if x_device_id and sess.device_id != x_device_id:
            raise HTTPException(status_code=409, detail='Session is locked to another device')
    now = datetime.now(timezone.utc)
    if tss.phase != 'intermission' or (tss.intermission_end_at and now < tss.intermission_end_at):
        raise HTTPException(status_code=400, detail='Intermission not finished')
    # start run
    ts = db.query(TryoutSetModel).filter(TryoutSetModel.id == tss.tryout_set_id).first()
    tss.phase = 'running'
    tss.run_start_at = now
    tss.run_end_at = now + timedelta(minutes=ts.duration_minutes or 60)
    db.commit()
    return { 'ok': True, 'run_end_at': tss.run_end_at }

@router.post('/set-sessions/{tss_id}/answer')
def submit_answer(
    tss_id: int,
    question_id: int,
    selected_answer: Optional[str] = None,
    essay_answer: Optional[str] = None,
    request: Request = None,
    x_device_id: Optional[str] = Header(None, alias='X-Device-Id'),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # basic guard
    tss = db.query(TryoutSetSessionModel).filter(TryoutSetSessionModel.id == tss_id).first()
    if not tss: raise HTTPException(status_code=404, detail='Set session not found')
    sess = db.query(TryoutSessionModel).filter(TryoutSessionModel.id == tss.tryout_session_id, TryoutSessionModel.user_id == user.id).first()
    if not sess: raise HTTPException(status_code=403, detail='Forbidden')
    # Disallow answering outside of running window or after time is up
    now = datetime.now(timezone.utc)
    if tss.phase != 'running':
        raise HTTPException(status_code=400, detail='Not accepting answers')
    if tss.run_end_at and now >= tss.run_end_at:
        raise HTTPException(status_code=400, detail='Time is up')
    # fetch question and compute correctness
    q = db.query(QuestionModel).filter(QuestionModel.id == question_id).first()
    if not q: raise HTTPException(status_code=404, detail='Question not found')
    # normalize selected and correct
    corr = False
    t = (q.question_type or 'mcq')
    # For essays, accept 'essay_answer' alias from client; store into selected_answer column
    if t == 'essay' and (essay_answer is not None):
        sel = (essay_answer or '').strip()
    else:
        sel = (selected_answer or '').strip()
    if t == 'multi':
        def as_set(s: str):
            return set([x.strip().upper() for x in (s or '').replace(';', ',').split(',') if x.strip()])
        corr = as_set(sel) == as_set(q.correct_answer or '')
    elif t == 'essay':
        corr = False
    else:
        corr = sel.upper() == (q.correct_answer or '').upper()
    # Use upsert to avoid duplicates
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    stmt = pg_insert(TryoutAnswerModel.__table__).values(
        tryout_set_session_id=tss_id,
        question_id=question_id,
        selected_answer=sel,
        is_correct=corr,
    )
    stmt = stmt.on_conflict_do_update(
        constraint='uq_tryout_answers_tss_q',
        set_=dict(selected_answer=sel, is_correct=corr)
    )
    db.execute(stmt)
    db.commit()
    return { 'ok': True }

@router.get('/set-sessions/{tss_id}/answers')
def get_existing_answers(
    tss_id: int,
    request: Request,
    x_device_id: Optional[str] = Header(None, alias='X-Device-Id'),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # validate ownership via parent session
    tss = db.query(TryoutSetSessionModel).filter(TryoutSetSessionModel.id == tss_id).first()
    if not tss: raise HTTPException(status_code=404, detail='Set session not found')
    sess = db.query(TryoutSessionModel).filter(
        TryoutSessionModel.id == tss.tryout_session_id,
        TryoutSessionModel.user_id == user.id
    ).first()
    if not sess: raise HTTPException(status_code=403, detail='Forbidden')
    if getattr(sess, 'device_id', None):
        if x_device_id and sess.device_id != x_device_id:
            raise HTTPException(status_code=409, detail='Session is locked to another device')
    rows = db.query(TryoutAnswerModel).filter(TryoutAnswerModel.tryout_set_session_id == tss_id).all()
    return { 'answers': [ { 'question_id': r.question_id, 'selected_answer': r.selected_answer } for r in rows ] }

@router.post('/set-sessions/{tss_id}/finish')
def finish_set(
    tss_id: int,
    request: Request,
    x_device_id: Optional[str] = Header(None, alias='X-Device-Id'),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    tss = db.query(TryoutSetSessionModel).filter(TryoutSetSessionModel.id == tss_id).first()
    if not tss: raise HTTPException(status_code=404, detail='Set session not found')
    sess = db.query(TryoutSessionModel).filter(TryoutSessionModel.id == tss.tryout_session_id, TryoutSessionModel.user_id == user.id).first()
    if not sess: raise HTTPException(status_code=403, detail='Forbidden')
    if getattr(sess, 'device_id', None):
        if x_device_id and sess.device_id != x_device_id:
            raise HTTPException(status_code=409, detail='Session is locked to another device')
    # finalize this set + compute score
    # total questions for this set
    ts = db.query(TryoutSetModel).filter(TryoutSetModel.id == tss.tryout_set_id).first()
    total = db.query(QuestionModel).filter(QuestionModel.question_set_id == ts.question_set_id).count()
    answered = db.query(TryoutAnswerModel).filter(TryoutAnswerModel.tryout_set_session_id == tss.id).count()
    correct = db.query(TryoutAnswerModel).filter(TryoutAnswerModel.tryout_set_session_id == tss.id, TryoutAnswerModel.is_correct == True).count()
    pct = (correct / total * 100.0) if total else 0.0
    tss.answered_count = answered
    tss.correct_count = correct
    tss.score_percentage = pct
    tss.phase = 'finished'
    db.commit()
    # find next set
    next_set = db.query(TryoutSetModel).filter(TryoutSetModel.tryout_id == ts.tryout_id, TryoutSetModel.order_index > ts.order_index).order_by(TryoutSetModel.order_index.asc()).first()
    if next_set:
        now = datetime.now(timezone.utc)
        inter_end = now + timedelta(seconds=60)
        next_tss = TryoutSetSessionModel(tryout_session_id=sess.id, tryout_set_id=next_set.id, phase='intermission', intermission_start_at=now, intermission_end_at=inter_end)
        db.add(next_tss); db.commit()
        return { 'next_tss_id': next_tss.id }
    else:
        sess.status = 'finished'; sess.finished_at = datetime.now(timezone.utc)
        db.commit()
        return { 'done': True }

@router.get('/sessions/{session_id}/result', response_model=TryoutResult)
def get_tryout_result(session_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    sess = db.query(TryoutSessionModel).filter(TryoutSessionModel.id == session_id, TryoutSessionModel.user_id == user.id).first()
    if not sess: raise HTTPException(status_code=404, detail='Session not found')
    # collect per-set sessions
    tsses = db.query(TryoutSetSessionModel).filter(TryoutSetSessionModel.tryout_session_id == session_id).all()
    out: List[TryoutResultSet] = []
    total_pct = 0.0
    n = 0
    correct_total = 0
    objective_total = 0
    set_ids: List[int] = []
    qset_ids: List[int] = []
    for s in tsses:
        ts = db.query(TryoutSetModel).filter(TryoutSetModel.id == s.tryout_set_id).first()
        if not ts:
            # Set removed; skip this set session
            continue
        # Resolve question set title for nicer display on frontend
        qs = db.query(QuestionSetModel).filter(QuestionSetModel.id == ts.question_set_id).first() if ts else None
        title = qs.title if qs and qs.title else None

        # --- Per-set breakdown ---
        qset_id = ts.question_set_id if ts else 0
        # Objective questions in this set
        obj_total = db.query(QuestionModel).filter(QuestionModel.question_set_id == qset_id, QuestionModel.question_type.in_(["mcq", "multi"])) .count()
        # Answers for this set session joined with Question to filter types
        from app.db.models import TryoutAnswer as TryoutAnswerModel, EssayGrade as EssayGradeModel
        # Objective answered and correct
        obj_answered = (
            db.query(TryoutAnswerModel)
            .join(QuestionModel, TryoutAnswerModel.question_id == QuestionModel.id)
            .filter(TryoutAnswerModel.tryout_set_session_id == s.id, QuestionModel.question_set_id == qset_id, QuestionModel.question_type.in_(["mcq", "multi"]))
            .count()
        )
        obj_correct = (
            db.query(TryoutAnswerModel)
            .join(QuestionModel, TryoutAnswerModel.question_id == QuestionModel.id)
            .filter(TryoutAnswerModel.tryout_set_session_id == s.id, QuestionModel.question_set_id == qset_id, QuestionModel.question_type.in_(["mcq", "multi"]), TryoutAnswerModel.is_correct == True)
            .count()
        )
        obj_pct = (obj_correct / obj_total * 100.0) if obj_total else 0.0

        # Essay metrics for this set
        essay_total = db.query(QuestionModel).filter(QuestionModel.question_set_id == qset_id, QuestionModel.question_type == "essay").count()
        # Essay answers for this set
        essay_answer_ids_q = (
            db.query(TryoutAnswerModel.id)
            .join(QuestionModel, TryoutAnswerModel.question_id == QuestionModel.id)
            .filter(TryoutAnswerModel.tryout_set_session_id == s.id, QuestionModel.question_set_id == qset_id, QuestionModel.question_type == "essay")
        )
        essay_answered = essay_answer_ids_q.count()
        essay_answer_ids = [row.id for row in essay_answer_ids_q.all()]
        essay_graded = 0
        essay_avg = 0.0
        if essay_answer_ids:
            grades = db.query(EssayGradeModel).filter(EssayGradeModel.tryout_answer_id.in_(essay_answer_ids)).all()
            scores = [g.score for g in grades if g and g.score is not None]
            # Count unanswered essays as auto-graded 0
            missing = max(0, (essay_total or 0) - (essay_answered or 0))
            essay_graded = len(scores) + missing
            if essay_total:
                essay_avg = float(sum(scores)) / float(essay_total)
            else:
                essay_avg = 0.0
        else:
            # No answers recorded; all essays are treated as graded 0
            essay_graded = essay_total
            essay_avg = 0.0

        payload = TryoutResultSet(
            order_index=db.query(TryoutSetModel.order_index).filter(TryoutSetModel.id==s.tryout_set_id).scalar() or 0,
            question_set_id=qset_id,
            answered_count=s.answered_count,
            correct_count=s.correct_count,
            score_percentage=s.score_percentage,
            title=title,
            objective_total_questions=obj_total,
            objective_answered_count=obj_answered,
            objective_correct_count=obj_correct,
            objective_score_percentage=obj_pct,
            essay_total_questions=essay_total,
            essay_answered_count=essay_answered,
            essay_graded_count=essay_graded,
            essay_avg_score=essay_avg,
        )
        out.append(payload)
        if s.score_percentage is not None:
            total_pct += float(s.score_percentage or 0.0)
            n += 1
        correct_total += int(s.correct_count or 0)
        set_ids.append(s.id)
        qset_ids.append(ts.question_set_id)
    if qset_ids:
        objective_total = db.query(QuestionModel).filter(QuestionModel.question_set_id.in_(qset_ids), QuestionModel.question_type.in_(["mcq", "multi"])) .count()
    overall = (total_pct / n) if n else 0.0
    # Essay metrics
    essay_count = 0
    essay_graded_count = 0
    essay_avg_score = 0.0
    if qset_ids:
        essay_count = db.query(QuestionModel).filter(QuestionModel.question_set_id.in_(qset_ids), QuestionModel.question_type == "essay").count()
    from app.db.models import EssayGrade as EssayGradeModel, TryoutAnswer as TryoutAnswerModel
    if set_ids:
        q = (
            db.query(TryoutAnswerModel.id)
            .join(QuestionModel, TryoutAnswerModel.question_id == QuestionModel.id)
            .filter(TryoutAnswerModel.tryout_set_session_id.in_(set_ids), QuestionModel.question_type == "essay")
        )
        essay_answer_ids = [row.id for row in q.all()]
        if essay_answer_ids:
            grades = db.query(EssayGradeModel).filter(EssayGradeModel.tryout_answer_id.in_(essay_answer_ids)).all()
            scores = [g.score for g in grades if g and g.score is not None]
            missing_total = max(0, essay_count - len(essay_answer_ids))
            essay_graded_count = len(scores) + missing_total
            if essay_count:
                essay_avg_score = float(sum(scores)) / float(essay_count)
            else:
                essay_avg_score = 0.0
        else:
            # No essay answers at all; consider all as graded 0
            essay_graded_count = essay_count
            essay_avg_score = 0.0

    score_percentage = (correct_total / max(1, objective_total)) * 100.0
    return TryoutResult(
        tryout_session_id=session_id,
        tryout_id=sess.tryout_id,
        sets=sorted(out, key=lambda x: x.order_index),
        overall_score=overall,
        total_questions=objective_total,
        correct_answers=correct_total,
        score_percentage=score_percentage,
        essay_count=essay_count,
        essay_graded_count=essay_graded_count,
        essay_avg_score=essay_avg_score,
    )

# ---------- History ----------
@router.get('/sessions/history')
def get_tryout_history(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    limit: int = 100,
    offset: int = 0,
):
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    # Fetch user's tryout sessions
    q = (
        db.query(TryoutSessionModel)
        .filter(TryoutSessionModel.user_id == user.id)
        .order_by(TryoutSessionModel.started_at.desc())
        .offset(offset)
        .limit(limit)
    )
    sessions = q.all()
    out = []
    for sess in sessions:
        # Sum correct across set sessions
        set_rows = db.query(TryoutSetSessionModel).filter(TryoutSetSessionModel.tryout_session_id == sess.id).all()
        correct_total = sum(int(s.correct_count or 0) for s in set_rows)
        # Count objective questions across all sets in this session
        qset_ids = []
        for s in set_rows:
            ts = db.query(TryoutSetModel).filter(TryoutSetModel.id == s.tryout_set_id).first()
            if ts:
                qset_ids.append(ts.question_set_id)
        objective_total = 0
        if qset_ids:
            objective_total = db.query(QuestionModel).filter(QuestionModel.question_set_id.in_(qset_ids), QuestionModel.question_type.in_(["mcq","multi"])) .count()
        pct = (correct_total / max(1, objective_total)) * 100.0
        # Resolve tryout title
        t = db.query(TryoutModel).filter(TryoutModel.id == sess.tryout_id).first()
        out.append({
            'id': sess.id,
            'tryout_id': sess.tryout_id,
            'tryout_title': t.title if t else None,
            'started_at': sess.started_at,
            'completed_at': getattr(sess, 'finished_at', None),
            'total_questions': objective_total,
            'correct_answers': correct_total,
            'score_percentage': pct,
            'status': sess.status,
        })
    return out
