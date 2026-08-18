"""Add INTERACTIVE to messagetype enum

Revision ID: o2p3q4r5s6t7
Revises: a79d55598871
Create Date: 2026-08-18 14:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'o2p3q4r5s6t7'
down_revision = 'a79d55598871'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add INTERACTIVE to messagetype enum
    # PostgreSQL doesn't support IF NOT EXISTS with ALTER TYPE ADD VALUE
    # We'll try to add it and ignore if it already exists
    try:
        op.execute("ALTER TYPE messagetype ADD VALUE 'INTERACTIVE'")
    except Exception:
        # Value already exists, ignore
        pass


def downgrade() -> None:
    # Cannot remove enum values in PostgreSQL directly
    # Would need to create a new type without the value and migrate
    pass
