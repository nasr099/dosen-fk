"""
Allow multiple correct answers: change questions.correct_answer to TEXT

Revision ID: 20251025_0011
Revises: 20251025_0010
Create Date: 2025-10-25 07:59:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251025_0011'
down_revision = '20251025_0010'
branch_labels = None
depends_on = None

def upgrade() -> None:
    with op.batch_alter_table('questions') as batch_op:
        batch_op.alter_column('correct_answer',
                              existing_type=sa.String(length=1),
                              type_=sa.Text(),
                              existing_nullable=False)

def downgrade() -> None:
    with op.batch_alter_table('questions') as batch_op:
        batch_op.alter_column('correct_answer',
                              existing_type=sa.Text(),
                              type_=sa.String(length=1),
                              existing_nullable=False)
