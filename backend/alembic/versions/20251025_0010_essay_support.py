"""
Essay support: add question_type to questions; expand exam_answers.selected_answer to Text

Revision ID: 20251025_0010
Revises: 20251019_0009
Create Date: 2025-10-25 07:22:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251025_0010'
down_revision = '20251019_0009'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add question_type with default 'mcq'
    with op.batch_alter_table('questions') as batch_op:
        batch_op.add_column(sa.Column('question_type', sa.String(), nullable=False, server_default='mcq'))
    # Convert selected_answer to Text to store essay free text
    with op.batch_alter_table('exam_answers') as batch_op:
        batch_op.alter_column('selected_answer',
                              existing_type=sa.String(length=1),
                              type_=sa.Text(),
                              existing_nullable=True)

    # Optional: drop server_default to keep clean schema after data backfilled
    with op.batch_alter_table('questions') as batch_op:
        batch_op.alter_column('question_type', server_default=None)


def downgrade() -> None:
    # Revert selected_answer back to String(1)
    with op.batch_alter_table('exam_answers') as batch_op:
        batch_op.alter_column('selected_answer',
                              existing_type=sa.Text(),
                              type_=sa.String(length=1),
                              existing_nullable=True)
    # Remove question_type
    with op.batch_alter_table('questions') as batch_op:
        batch_op.drop_column('question_type')
