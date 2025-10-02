from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: Optional[bool] = True

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class QuestionBase(BaseModel):
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    option_e: str
    correct_answer: str
    explanation: Optional[str] = None
    is_featured: Optional[bool] = False
    is_active: Optional[bool] = True
    difficulty_level: Optional[str] = "medium"

# Bare question payload for nested set creation (no category_id / set_id)
class QuestionBareCreate(QuestionBase):
    pass

class QuestionCreate(QuestionBase):
    category_id: int
    question_set_id: Optional[int] = None

class QuestionUpdate(QuestionBase):
    category_id: Optional[int] = None
    question_set_id: Optional[int] = None

class Question(QuestionBase):
    id: int
    category_id: int
    question_set_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    category: Optional[Category] = None

    class Config:
        from_attributes = True

class QuestionForExam(BaseModel):
    id: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    option_e: str
    difficulty_level: str

    class Config:
        from_attributes = True
