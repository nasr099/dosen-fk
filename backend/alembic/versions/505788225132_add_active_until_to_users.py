"""
add active_until to users

Revision ID: 505788225132
Revises: 20250929_0003_add_posts
Create Date: 2025-10-02
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '505788225132'
down_revision = '20250929_0003_add_posts'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('active_until', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('active_until')
