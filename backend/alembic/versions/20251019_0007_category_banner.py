"""
Add banner_url to categories

Revision ID: 20251019_0007
Revises: 20251019_0006
Create Date: 2025-10-19 07:38:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251019_0007'
down_revision = '20251019_0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('categories', sa.Column('banner_url', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('categories', 'banner_url')
