from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.question import QuestionBareCreate

class QuestionSetBase(BaseModel):
    category_id: int
    title: str
    description: Optional[str] = None
    time_limit_minutes: int = 60
    is_active: bool = True
    # free | paid
    access_level: str = "free"
    # availability flags
    allow_in_exam: bool = True
    allow_in_tryout: bool = False

class QuestionSetCreate(QuestionSetBase):
    pass

class QuestionSetUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    time_limit_minutes: Optional[int] = None
    is_active: Optional[bool] = None
    access_level: Optional[str] = None
    allow_in_exam: Optional[bool] = None
    allow_in_tryout: Optional[bool] = None

class QuestionSet(QuestionSetBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class QuestionSetWithQuestionsCreate(QuestionSetCreate):
    questions: List[QuestionBareCreate]

class QuestionSetWithQuestionsUpdate(QuestionSetUpdate):
    questions: List[QuestionBareCreate]
