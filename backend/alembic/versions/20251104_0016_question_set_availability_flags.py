"""
Add allow_in_exam and allow_in_tryout flags to question_sets

Revision ID: 20251104_0016
Revises: 20251101_0015
Create Date: 2025-11-04
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251104_0016'
down_revision = '20251101_0015'
branch_labels = None
depends_on = None

def upgrade() -> None:
    with op.batch_alter_table('question_sets') as batch:
        # Use PostgreSQL boolean literals true/false for server defaults
        batch.add_column(sa.Column('allow_in_exam', sa.Boolean(), server_default=sa.text('true'), nullable=False))
        batch.add_column(sa.Column('allow_in_tryout', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    # Optional: drop server defaults to avoid future implicit defaults at DB level
    with op.batch_alter_table('question_sets') as batch:
        batch.alter_column('allow_in_exam', server_default=None)
        batch.alter_column('allow_in_tryout', server_default=None)


def downgrade() -> None:
    with op.batch_alter_table('question_sets') as batch:
        batch.drop_column('allow_in_tryout')
        batch.drop_column('allow_in_exam')
