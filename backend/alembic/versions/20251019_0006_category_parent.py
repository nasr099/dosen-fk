"""
Add parent_id to categories and seed head categories

Revision ID: 20251019_0006
Revises: 20251018_0005
Create Date: 2025-10-19 07:19:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '20251019_0006'
down_revision = '20251018_0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('categories', sa.Column('parent_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_categories_parent', 'categories', 'categories', ['parent_id'], ['id'])
    op.create_index('ix_categories_parent_id', 'categories', ['parent_id'])

    # Seed head categories if not present
    conn = op.get_bind()
    heads = [
        'Persiapan Masuk Kedokteran',
        'Pendidikan Dokter Umum',
        'Persiapan Pendidikan Spesialis',
    ]
    for name in heads:
        exists = conn.execute(text("SELECT id FROM categories WHERE name=:n"), {"n": name}).fetchone()
        if not exists:
            conn.execute(text("INSERT INTO categories (name, description, is_active) VALUES (:n, '', true)"), {"n": name})


def downgrade() -> None:
    op.drop_index('ix_categories_parent_id', table_name='categories')
    op.drop_constraint('fk_categories_parent', 'categories', type_='foreignkey')
    op.drop_column('categories', 'parent_id')
