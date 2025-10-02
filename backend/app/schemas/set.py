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

class QuestionSetCreate(QuestionSetBase):
    pass

class QuestionSetUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    time_limit_minutes: Optional[int] = None
    is_active: Optional[bool] = None

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
