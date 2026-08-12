"""Fix product_categories is_active column

Revision ID: l3m4n5o6p7q8
Revises: k1l2m3n4o5p6
Create Date: 2026-08-10 20:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'l3m4n5o6p7q8'
down_revision = 'k1l2m3n4o5p6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_active column to product_categories if it doesn't exist
    try:
        op.add_column('product_categories', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    except Exception:
        # Column might already exist
        pass


def downgrade() -> None:
    # Remove is_active column
    try:
        op.drop_column('product_categories', 'is_active')
    except Exception:
        pass
