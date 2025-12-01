"""
Performance indexes for frequent lookups

Revision ID: 20251029_0014_perf_indexes
Revises: 20251026_0013_add_is_teacher_to_users
Create Date: 2025-10-29
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251029_0014_perf_indexes'
down_revision = '20251026_0013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Questions: filter by question_set_id, category_id
    op.create_index('ix_questions_question_set_id', 'questions', ['question_set_id'], unique=False)
    op.create_index('ix_questions_category_id', 'questions', ['category_id'], unique=False)

    # Question sets: filter by category
    op.create_index('ix_question_sets_category_id', 'question_sets', ['category_id'], unique=False)

    # Exam sessions: filter by user and set
    op.create_index('ix_exam_sessions_user_id', 'exam_sessions', ['user_id'], unique=False)
    op.create_index('ix_exam_sessions_question_set_id', 'exam_sessions', ['question_set_id'], unique=False)
    op.create_index('ix_exam_sessions_started_at', 'exam_sessions', ['started_at'], unique=False)

    # Exam answers: by session and question
    op.create_index('ix_exam_answers_exam_session_id', 'exam_answers', ['exam_session_id'], unique=False)
    op.create_index('ix_exam_answers_question_id', 'exam_answers', ['question_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_exam_answers_question_id', table_name='exam_answers')
    op.drop_index('ix_exam_answers_exam_session_id', table_name='exam_answers')
    op.drop_index('ix_exam_sessions_started_at', table_name='exam_sessions')
    op.drop_index('ix_exam_sessions_question_set_id', table_name='exam_sessions')
    op.drop_index('ix_exam_sessions_user_id', table_name='exam_sessions')
    op.drop_index('ix_question_sets_category_id', table_name='question_sets')
    op.drop_index('ix_questions_category_id', table_name='questions')
    op.drop_index('ix_questions_question_set_id', table_name='questions')
