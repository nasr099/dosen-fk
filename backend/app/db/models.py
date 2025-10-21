from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    active_until = Column(DateTime(timezone=True), nullable=True)
    is_admin = Column(Boolean, default=False)
    # free | paid
    plan = Column(String, default="free")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    exam_sessions = relationship("ExamSession", back_populates="user")

class ZoomDiscussion(Base):
    __tablename__ = "zoom_discussions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    presenter_name = Column(String, nullable=False)
    description = Column(Text)
    image_url = Column(String)
    start_at = Column(DateTime(timezone=True), nullable=False)
    end_at = Column(DateTime(timezone=True))
    # optional link to a sub-category
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    meeting_url = Column(String)  # protected: only for paid users
    meeting_password = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    excerpt = Column(Text)
    content_html = Column(Text, nullable=False)
    cover_url = Column(String)
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime(timezone=True))
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    # Head/Sub hierarchy
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    banner_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    parent = relationship("Category", remote_side=[id], backref="children")
    questions = relationship("Question", back_populates="category")
    question_sets = relationship("QuestionSet", back_populates="category")

class QuestionSet(Base):
    __tablename__ = "question_sets"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    time_limit_minutes = Column(Integer, default=60)
    is_active = Column(Boolean, default=True)
    # free | paid
    access_level = Column(String, default="free")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    category = relationship("Category", back_populates="question_sets")
    questions = relationship("Question", back_populates="question_set")

class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    headline = Column(Text)
    quote = Column(Text)
    photo_url = Column(String)
    linkedin = Column(String)
    twitter = Column(String)
    website = Column(String)
    display_order = Column(Integer, default=0)
    is_visible = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    question_set_id = Column(Integer, ForeignKey("question_sets.id"), nullable=True)
    question_text = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=False)
    option_e = Column(Text, nullable=False)
    correct_answer = Column(String(1), nullable=False)  # A, B, C, D, or E
    explanation = Column(Text)
    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    difficulty_level = Column(String, default="medium")  # easy, medium, hard
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    category = relationship("Category", back_populates="questions")
    question_set = relationship("QuestionSet", back_populates="questions")
    exam_answers = relationship("ExamAnswer", back_populates="question")

class ExamSession(Base):
    __tablename__ = "exam_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    question_set_id = Column(Integer, ForeignKey("question_sets.id"), nullable=True)
    total_questions = Column(Integer, nullable=False)
    correct_answers = Column(Integer, default=0)
    score_percentage = Column(Float, default=0.0)
    time_limit_minutes = Column(Integer, default=60)
    time_taken_minutes = Column(Float)
    is_completed = Column(Boolean, default=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="exam_sessions")
    exam_answers = relationship("ExamAnswer", back_populates="exam_session")

class ExamAnswer(Base):
    __tablename__ = "exam_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    exam_session_id = Column(Integer, ForeignKey("exam_sessions.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    selected_answer = Column(String(1))  # A, B, C, D, E, or null if not answered
    is_correct = Column(Boolean, default=False)
    answered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    exam_session = relationship("ExamSession", back_populates="exam_answers")
    question = relationship("Question", back_populates="exam_answers")

class PromoBanner(Base):
    __tablename__ = "promo_banners"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    image_url = Column(String)
    link_url = Column(String)
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
