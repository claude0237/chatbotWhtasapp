"""Merge migration heads

Revision ID: merge1
Revises: n1o2p3q4r5s6, l3m4n5o6p7q8
Create Date: 2026-08-11

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'merge1'
down_revision = ('n1o2p3q4r5s6', 'l3m4n5o6p7q8')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
