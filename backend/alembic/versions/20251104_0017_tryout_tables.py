"""
Create tryout core tables

Revision ID: 20251104_0017
Revises: 20251104_0016
Create Date: 2025-11-04
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251104_0017'
down_revision = '20251104_0016'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'tryouts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        'tryout_sets',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tryout_id', sa.Integer(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('question_set_id', sa.Integer(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('intermission_text', sa.Text()),
    )
    op.create_index('ix_tryout_sets_tryout_id', 'tryout_sets', ['tryout_id'])
    op.create_table(
        'tryout_sessions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tryout_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), server_default=sa.text("'running'"), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_tryout_sessions_tryout_id', 'tryout_sessions', ['tryout_id'])
    op.create_index('ix_tryout_sessions_user_id', 'tryout_sessions', ['user_id'])
    op.create_table(
        'tryout_set_sessions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tryout_session_id', sa.Integer(), nullable=False),
        sa.Column('tryout_set_id', sa.Integer(), nullable=False),
        sa.Column('phase', sa.String(), server_default=sa.text("'intermission'"), nullable=False),
        sa.Column('intermission_start_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('intermission_end_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('run_start_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('run_end_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('answered_count', sa.Integer(), server_default='0'),
        sa.Column('correct_count', sa.Integer(), server_default='0'),
        sa.Column('score_percentage', sa.Float(), server_default='0'),
    )
    op.create_index('ix_tss_session', 'tryout_set_sessions', ['tryout_session_id'])
    op.create_index('ix_tss_set', 'tryout_set_sessions', ['tryout_set_id'])
    op.create_table(
        'tryout_answers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tryout_set_session_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('selected_answer', sa.Text()),
        sa.Column('is_correct', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('answered_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_ta_session', 'tryout_answers', ['tryout_set_session_id'])
    op.create_index('ix_ta_question', 'tryout_answers', ['question_id'])


def downgrade() -> None:
    op.drop_index('ix_ta_question', table_name='tryout_answers')
    op.drop_index('ix_ta_session', table_name='tryout_answers')
    op.drop_table('tryout_answers')
    op.drop_index('ix_tss_set', table_name='tryout_set_sessions')
    op.drop_index('ix_tss_session', table_name='tryout_set_sessions')
    op.drop_table('tryout_set_sessions')
    op.drop_index('ix_tryout_sessions_user_id', table_name='tryout_sessions')
    op.drop_index('ix_tryout_sessions_tryout_id', table_name='tryout_sessions')
    op.drop_table('tryout_sessions')
    op.drop_index('ix_tryout_sets_tryout_id', table_name='tryout_sets')
    op.drop_table('tryout_sets')
    op.drop_table('tryouts')
