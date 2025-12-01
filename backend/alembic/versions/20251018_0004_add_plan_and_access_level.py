"""add plan to users and access_level to question_sets

Revision ID: 20251018_0004
Revises: 9ca99089147d
Create Date: 2025-10-18 03:51:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251018_0004'
down_revision = '9ca99089147d'
branch_labels = None
depends_on = None

def upgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('plan', sa.String(), server_default='free'))
    with op.batch_alter_table('question_sets') as batch_op:
        batch_op.add_column(sa.Column('access_level', sa.String(), server_default='free'))

    # Optional: drop server_default after backfill so future rows rely on app defaults
    op.execute("ALTER TABLE users ALTER COLUMN plan DROP DEFAULT;")
    op.execute("ALTER TABLE question_sets ALTER COLUMN access_level DROP DEFAULT;")


def downgrade() -> None:
    with op.batch_alter_table('question_sets') as batch_op:
        batch_op.drop_column('access_level')
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('plan')
