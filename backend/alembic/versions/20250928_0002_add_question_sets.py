"""add question sets

Revision ID: 20250928_0002_add_question_sets
Revises: 20250928_0001_init
Create Date: 2025-09-28 07:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20250928_0002_add_question_sets'
down_revision: Union[str, None] = '20250928_0001_init'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'question_sets',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('categories.id'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('time_limit_minutes', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.add_column('questions', sa.Column('question_set_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_questions_set', 'questions', 'question_sets', ['question_set_id'], ['id'])

    op.add_column('exam_sessions', sa.Column('question_set_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_examsession_set', 'exam_sessions', 'question_sets', ['question_set_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_examsession_set', 'exam_sessions', type_='foreignkey')
    op.drop_column('exam_sessions', 'question_set_id')

    op.drop_constraint('fk_questions_set', 'questions', type_='foreignkey')
    op.drop_column('questions', 'question_set_id')

    op.drop_table('question_sets')
