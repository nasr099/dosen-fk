"""
Add category_id to zoom_discussions

Revision ID: 20251019_0009
Revises: 20251019_0008
Create Date: 2025-10-19 09:33:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251019_0009'
down_revision = '20251019_0008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('zoom_discussions', sa.Column('category_id', sa.Integer(), nullable=True))
    op.create_index('ix_zoom_discussions_category_id', 'zoom_discussions', ['category_id'])
    op.create_foreign_key('fk_zoom_discussions_category', 'zoom_discussions', 'categories', ['category_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_zoom_discussions_category', 'zoom_discussions', type_='foreignkey')
    op.drop_index('ix_zoom_discussions_category_id', table_name='zoom_discussions')
    op.drop_column('zoom_discussions', 'category_id')
