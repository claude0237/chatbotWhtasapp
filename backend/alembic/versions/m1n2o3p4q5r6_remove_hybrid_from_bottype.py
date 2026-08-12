"""Remove HYBRID from bottype enum

Revision ID: m1n2o3p4q5r6
Revises: 1105bc2d30f6
Create Date: 2026-08-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'm1n2o3p4q5r6'
down_revision = '1105bc2d30f6'
branch_labels = None
depends_on = None


def upgrade():
    # Update any existing HYBRID records to NATIVE (since NATIVE now has ML fallback)
    op.execute("UPDATE bot_configurations SET bot_type = 'NATIVE' WHERE bot_type = 'HYBRID'")
    # Note: The PostgreSQL enum 'HYBRID' value will remain in the database but won't be used
    # since the Python enum no longer includes it and all records have been converted to NATIVE


def downgrade():
    # Convert NATIVE back to HYBRID if needed (not recommended)
    pass
