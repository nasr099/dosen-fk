"""
Add essay_grades table for manual grading (0-100)

Revision ID: 20251026_0012
Revises: 20251025_0011
Create Date: 2025-10-26 00:00:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251026_0012'
down_revision = '20251025_0011'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'essay_grades',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('exam_answer_id', sa.Integer(), sa.ForeignKey('exam_answers.id'), nullable=False, index=True),
        sa.Column('score', sa.Integer(), nullable=False),  # 0-100
        sa.Column('status', sa.String(), nullable=False, server_default='approved'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('graded_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('graded_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    # Optional index for faster admin queries
    op.create_index('ix_essay_grades_answer', 'essay_grades', ['exam_answer_id'])

    # Clean default after creation to keep schema tidy
    with op.batch_alter_table('essay_grades') as batch_op:
        batch_op.alter_column('status', server_default=None)


def downgrade() -> None:
    op.drop_index('ix_essay_grades_answer', table_name='essay_grades')
    op.drop_table('essay_grades')
