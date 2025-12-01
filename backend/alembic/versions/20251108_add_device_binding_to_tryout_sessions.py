"""
add device binding columns to tryout_sessions

Revision ID: 20251108_add_device_binding
Revises: 
Create Date: 2025-11-08 14:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251108_add_device_binding'
down_revision = '20251108_tryout_meta'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('tryout_sessions') as batch_op:
        batch_op.add_column(sa.Column('device_id', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('user_agent', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('started_ip', sa.String(), nullable=True))
        batch_op.create_index('ix_tryout_sessions_device_id', ['device_id'], unique=False)


def downgrade():
    with op.batch_alter_table('tryout_sessions') as batch_op:
        try:
            batch_op.drop_index('ix_tryout_sessions_device_id')
        except Exception:
            pass
        batch_op.drop_column('started_ip')
        batch_op.drop_column('user_agent')
        batch_op.drop_column('device_id')
