"""
Sync users.is_active from plan and active_until via DB trigger

Revision ID: 20251018_0005
Revises: 20251018_0004
Create Date: 2025-10-18 04:36:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251018_0005'
down_revision = '20251018_0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create a function to compute is_active from plan/active_until
    op.execute(
        sa.text(
            """
            CREATE OR REPLACE FUNCTION public.users_sync_active_from_plan()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            DECLARE
                now_utc timestamptz := (now() AT TIME ZONE 'UTC');
            BEGIN
                -- If plan is paid and active_until is in the future => active, else inactive
                IF NEW.plan = 'paid' AND NEW.active_until IS NOT NULL AND NEW.active_until > now_utc THEN
                    NEW.is_active := TRUE;
                ELSE
                    NEW.is_active := FALSE;
                END IF;
                RETURN NEW;
            END;
            $$;
            """
        )
    )
    # Create trigger on insert and update of plan/active_until
    op.execute(
        sa.text(
            """
            DROP TRIGGER IF EXISTS trg_users_sync_active ON public.users;
            CREATE TRIGGER trg_users_sync_active
            BEFORE INSERT OR UPDATE OF plan, active_until ON public.users
            FOR EACH ROW
            EXECUTE FUNCTION public.users_sync_active_from_plan();
            """
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP TRIGGER IF EXISTS trg_users_sync_active ON public.users;"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS public.users_sync_active_from_plan();"))
