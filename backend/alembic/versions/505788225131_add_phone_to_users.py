"""add phone to users

Revision ID: 505788225131
Revises: 20250928_0002_add_question_sets
Create Date: 2025-09-29 09:49:55.712914

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '505788225131'
down_revision = '20250928_0002_add_question_sets'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('phone', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'phone')
