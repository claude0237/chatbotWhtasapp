"""Add MISTRAL to mlprovider enum

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2026-08-10 20:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'k1l2m3n4o5p6'
down_revision = 'j0k1l2m3n4o5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add MISTRAL to mlprovider enum
    # PostgreSQL doesn't support IF NOT EXISTS with ALTER TYPE ADD VALUE
    # We'll try to add it and ignore if it already exists
    try:
        op.execute("ALTER TYPE mlprovider ADD VALUE 'MISTRAL'")
    except Exception:
        # Value already exists, ignore
        pass


def downgrade() -> None:
    # Cannot remove enum values in PostgreSQL directly
    # Would need to create a new type without the value and migrate
    pass
