from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ExamSessionBase(BaseModel):
    category_id: int
    question_set_id: Optional[int] = None
    time_limit_minutes: Optional[int] = 60

class ExamSessionCreate(ExamSessionBase):
    pass

class ExamSession(ExamSessionBase):
    id: int
    user_id: int
    total_questions: int
    correct_answers: int
    score_percentage: float
    time_taken_minutes: Optional[float] = None
    is_completed: bool
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ExamAnswerBase(BaseModel):
    question_id: int
    selected_answer: Optional[str] = None

class ExamAnswerCreate(ExamAnswerBase):
    exam_session_id: int

class ExamAnswer(ExamAnswerBase):
    id: int
    exam_session_id: int
    is_correct: bool
    answered_at: datetime

    class Config:
        from_attributes = True

class ExamSubmission(BaseModel):
    exam_session_id: int
    answers: List[ExamAnswerBase]
    time_taken_minutes: float

class ExamResult(BaseModel):
    exam_session_id: int
    total_questions: int  # objective questions count (mcq + multi)
    correct_answers: int
    score_percentage: float
    time_taken_minutes: float
    answers: List[dict]  # Detailed answer results with explanations
    # Essay grading summary
    essay_count: Optional[int] = None
    essay_graded_count: Optional[int] = None
    essay_avg_score: Optional[float] = None

# ---------- Essay grading ----------
class EssayGradePayload(BaseModel):
    score: int  # 0-100
    status: str  # approved | partial | incorrect
    notes: Optional[str] = None

class EssayGradePublic(BaseModel):
    id: int
    exam_answer_id: int
    score: int
    status: str
    notes: Optional[str] = None
    graded_by: Optional[int] = None
    graded_at: datetime

    class Config:
        from_attributes = True

class EssayAnswerItem(BaseModel):
    answer_id: int
    session_id: int
    user_id: int
    user_email: str
    set_id: Optional[int] = None
    set_title: Optional[str] = None
    question_id: int
    question_text: str
    user_answer: Optional[str] = None
    completed_at: Optional[datetime] = None
    grade: Optional[EssayGradePublic] = None

class EssayListResponse(BaseModel):
    total: int
    items: List[EssayAnswerItem]

class PromoBannerBase(BaseModel):
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    is_active: Optional[bool] = True
    display_order: Optional[int] = 0

class PromoBannerCreate(PromoBannerBase):
    pass

class PromoBannerUpdate(PromoBannerBase):
    pass

class PromoBanner(PromoBannerBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
