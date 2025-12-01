from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic. Keep <=32 chars
revision = '20251104_0019'
down_revision = '20251104_0018'
branch_labels = None
depends_on = None

def upgrade():
    # 1) Deduplicate existing data: keep the latest answer per (tss_id, question_id)
    op.execute(
        """
        WITH ranked AS (
            SELECT id,
                   ROW_NUMBER() OVER (
                       PARTITION BY tryout_set_session_id, question_id
                       ORDER BY answered_at DESC NULLS LAST, id DESC
                   ) AS rn
            FROM tryout_answers
        )
        DELETE FROM tryout_answers ta
        USING ranked r
        WHERE ta.id = r.id AND r.rn > 1;
        """
    )

    # 2) Add unique constraint to prevent duplicate answers for the same question in a set session
    op.create_unique_constraint(
        'uq_tryout_answers_tss_q',
        'tryout_answers',
        ['tryout_set_session_id', 'question_id']
    )


def downgrade():
    op.drop_constraint('uq_tryout_answers_tss_q', 'tryout_answers', type_='unique')
