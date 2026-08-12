"""Remove fallback_strategy column from bot_configurations

Revision ID: n1o2p3q4r5s6
Revises: m1n2o3p4q5r6
Create Date: 2026-08-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'n1o2p3q4r5s6'
down_revision = 'm1n2o3p4q5r6'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the fallback_strategy column
    op.drop_column('bot_configurations', 'fallback_strategy')


def downgrade():
    # Add back the fallback_strategy column
    # Note: This won't restore the enum type properly, but it's a simple rollback
    op.add_column('bot_configurations', sa.Column('fallback_strategy', sa.String(), nullable=True))
