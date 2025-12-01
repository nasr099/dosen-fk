from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic. Keep <=32 chars (alembic_version.version_num)
revision = '20251104_0018'
down_revision = '20251104_0017'
branch_labels = None
depends_on = None

def upgrade():
    # 1) make exam_answer_id nullable
    with op.batch_alter_table('essay_grades') as batch_op:
        batch_op.alter_column('exam_answer_id', existing_type=sa.Integer(), nullable=True)

    # 2) add tryout_answer_id column + index + FK to tryout_answers.id
    op.add_column('essay_grades', sa.Column('tryout_answer_id', sa.Integer(), nullable=True))
    op.create_index('ix_essay_grades_tryout_answer_id', 'essay_grades', ['tryout_answer_id'])
    op.create_foreign_key(
        'fk_essay_grades_tryout_answer_id_tryout_answers',
        'essay_grades', 'tryout_answers',
        ['tryout_answer_id'], ['id'],
        ondelete='CASCADE'
    )

    # Optional check constraint (Postgres only). Skip by default for cross-DB portability.
    # op.create_check_constraint(
    #     'ck_essay_grades_one_ref',
    #     'essay_grades',
    #     '(exam_answer_id IS NOT NULL) OR (tryout_answer_id IS NOT NULL)'
    # )


def downgrade():
    # reverse of upgrade
    # op.drop_constraint('ck_essay_grades_one_ref', 'essay_grades', type_='check')
    op.drop_constraint('fk_essay_grades_tryout_answer_id_tryout_answers', 'essay_grades', type_='foreignkey')
    op.drop_index('ix_essay_grades_tryout_answer_id', table_name='essay_grades')
    op.drop_column('essay_grades', 'tryout_answer_id')
    with op.batch_alter_table('essay_grades') as batch_op:
        batch_op.alter_column('exam_answer_id', existing_type=sa.Integer(), nullable=False)
