"""add team_members table

Revision ID: 9ca99089147d
Revises: 505788225132
Create Date: 2025-10-04 16:29:45.104666

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9ca99089147d'
down_revision = '505788225132'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Safe migration: only create the new team_members table
    op.create_table(
        'team_members',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('headline', sa.Text()),
        sa.Column('quote', sa.Text()),
        sa.Column('photo_url', sa.String()),
        sa.Column('linkedin', sa.String()),
        sa.Column('twitter', sa.String()),
        sa.Column('website', sa.String()),
        sa.Column('display_order', sa.Integer(), server_default=sa.text('0')),
        sa.Column('is_visible', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('team_members')
