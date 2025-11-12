from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class TryoutSetBase(BaseModel):
    question_set_id: int
    order_index: int
    duration_minutes: int
    intermission_text: Optional[str] = None

class TryoutBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_active: bool = True
    # Optional high-level category for this Tryout (separate from Questions category)
    category: Optional[str] = None

class TryoutCreate(TryoutBase):
    sets: List[TryoutSetBase] = []

class TryoutUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sets: Optional[List[TryoutSetBase]] = None
    category: Optional[str] = None

class Tryout(TryoutBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    sets: List[TryoutSetBase] = []

    class Config:
        from_attributes = True

class CurrentSetMeta(BaseModel):
    id: int
    order_index: int
    title: str
    duration_minutes: int
    question_set_id: int
    intermission_text: Optional[str] = None
    description: Optional[str] = None

class TryoutCurrentPhase(BaseModel):
    tryout_session_id: int
    tss_id: int
    order_index: int
    phase: str  # intermission | running | finished | done
    now: datetime
    intermission_end_at: Optional[datetime] = None
    run_end_at: Optional[datetime] = None
    set: Optional[CurrentSetMeta] = None

class TryoutResultSet(BaseModel):
    order_index: int
    question_set_id: int
    answered_count: int
    correct_count: int
    score_percentage: float
    title: Optional[str] = None
    # Objective (MCQ + Multi)
    objective_total_questions: int = 0
    objective_answered_count: int = 0
    objective_correct_count: int = 0
    objective_score_percentage: float = 0.0
    # Essays
    essay_total_questions: int = 0
    essay_answered_count: int = 0
    essay_graded_count: int = 0
    essay_avg_score: float = 0.0

class TryoutResult(BaseModel):
    tryout_session_id: int
    tryout_id: int
    sets: List[TryoutResultSet]
    overall_score: float
    total_questions: int = 0
    correct_answers: int = 0
    score_percentage: float = 0.0
    essay_count: int = 0
    essay_graded_count: int = 0
    essay_avg_score: float = 0.0
