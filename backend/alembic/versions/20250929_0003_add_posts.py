from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250929_0003_add_posts'
down_revision = '505788225131'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'posts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('excerpt', sa.Text()),
        sa.Column('content_html', sa.Text(), nullable=False),
        sa.Column('cover_url', sa.String()),
        sa.Column('is_published', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True)),
        sa.Column('author_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )
    op.create_unique_constraint('uq_posts_slug', 'posts', ['slug'])
    op.create_index('ix_posts_slug', 'posts', ['slug'])


def downgrade():
    op.drop_index('ix_posts_slug', table_name='posts')
    op.drop_constraint('uq_posts_slug', 'posts', type_='unique')
    op.drop_table('posts')
