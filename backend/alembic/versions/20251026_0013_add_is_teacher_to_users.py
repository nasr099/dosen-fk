"""
add is_teacher to users

Revision ID: 20251026_0013
Revises: 20251026_0012
Create Date: 2025-10-26
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251026_0013'
down_revision = '20251026_0012'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('is_teacher', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    # Drop server_default after setting for existing rows
    op.execute("ALTER TABLE users ALTER COLUMN is_teacher DROP DEFAULT")


def downgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('is_teacher')
