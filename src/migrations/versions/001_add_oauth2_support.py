"""Add OAuth2 support with oauth_token table and user oauth fields

Revision ID: 001_add_oauth2_support
Revises:
Create Date: 2026-01-07 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_oauth2_support'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### Create oauth_token table ###
    op.create_table(
        'oauth_token',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_type', sa.String(length=50), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('scopes', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_oauth_token_provider'), 'oauth_token', ['provider'], unique=False)
    op.create_index(op.f('ix_oauth_token_user_id'), 'oauth_token', ['user_id'], unique=False)

    # ### Add OAuth fields to user table ###
    op.add_column('user', sa.Column('oauth_provider', sa.String(length=50), nullable=True))
    op.add_column('user', sa.Column('oauth_sub', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_user_oauth_sub'), 'user', ['oauth_sub'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### Remove OAuth fields from user table ###
    op.drop_index(op.f('ix_user_oauth_sub'), table_name='user')
    op.drop_column('user', 'oauth_sub')
    op.drop_column('user', 'oauth_provider')

    # ### Drop oauth_token table ###
    op.drop_index(op.f('ix_oauth_token_user_id'), table_name='oauth_token')
    op.drop_index(op.f('ix_oauth_token_provider'), table_name='oauth_token')
    op.drop_table('oauth_token')
    # ### end Alembic commands ###
