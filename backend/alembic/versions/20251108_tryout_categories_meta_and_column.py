"""
Add tryout_categories table, tryout_meta table, and tryouts.category column

Revision ID: 20251108_tryout_meta
Revises: 
Create Date: 2025-11-08
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251108_tryout_meta'
down_revision = '20251104_0019'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1) Add category column to tryouts (nullable)
    try:
        op.add_column('tryouts', sa.Column('category', sa.String(), nullable=True))
    except Exception:
        # Column may already exist; ignore
        pass

    # 2) Create tryout_categories table (id, name unique)
    if not op.get_bind().dialect.has_table(op.get_bind(), 'tryout_categories'):
        op.create_table(
            'tryout_categories',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('name', sa.String(), nullable=False, unique=True, index=True),
        )

    # 3) Create tryout_meta table (id, tryout_id unique FK, category)
    if not op.get_bind().dialect.has_table(op.get_bind(), 'tryout_meta'):
        op.create_table(
            'tryout_meta',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('tryout_id', sa.Integer(), sa.ForeignKey('tryouts.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
            sa.Column('category', sa.String(), nullable=True),
        )


def downgrade() -> None:
    # Drop tryout_meta
    try:
        op.drop_table('tryout_meta')
    except Exception:
        pass

    # Drop tryout_categories
    try:
        op.drop_table('tryout_categories')
    except Exception:
        pass

    # Drop column from tryouts
    try:
        op.drop_column('tryouts', 'category')
    except Exception:
        pass
