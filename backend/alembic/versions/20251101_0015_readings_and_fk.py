"""
add readings table and reading_id fk on questions

Revision ID: 20251101_0015
Revises: 20251029_0014
Create Date: 2025-11-01
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251101_0015'
down_revision = '20251029_0014_perf_indexes'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'readings',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content_html', sa.Text(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    # Optional index for category_id
    op.create_index('ix_readings_category_id', 'readings', ['category_id'])

    # Add reading_id to questions
    op.add_column('questions', sa.Column('reading_id', sa.Integer(), nullable=True))
    op.create_index('ix_questions_reading_id', 'questions', ['reading_id'])
    op.create_foreign_key('fk_questions_reading_id', 'questions', 'readings', ['reading_id'], ['id'], ondelete='SET NULL')


def downgrade():
    op.drop_constraint('fk_questions_reading_id', 'questions', type_='foreignkey')
    op.drop_index('ix_questions_reading_id', table_name='questions')
    op.drop_column('questions', 'reading_id')

    op.drop_index('ix_readings_category_id', table_name='readings')
    op.drop_table('readings')
