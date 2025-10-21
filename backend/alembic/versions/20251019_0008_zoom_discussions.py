"""
Create zoom_discussions table

Revision ID: 20251019_0008
Revises: 20251019_0007
Create Date: 2025-10-19 08:45:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251019_0008'
down_revision = '20251019_0007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'zoom_discussions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('presenter_name', sa.String(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('image_url', sa.String()),
        sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_at', sa.DateTime(timezone=True)),
        sa.Column('meeting_url', sa.String()),
        sa.Column('meeting_password', sa.String()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table('zoom_discussions')
