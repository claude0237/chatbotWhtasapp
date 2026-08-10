"""add_whatsapp_tenant_configs

Revision ID: i9d0e1f2g3h4
Revises: h8c9d0e1f2g3
Create Date: 2026-08-07 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'i9d0e1f2g3h4'
down_revision: Union[str, None] = 'h8c9d0e1f2g3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This migration doesn't add new columns to the schema
    # The channel_configurations table already supports dynamic key-value pairs
    # We will add default configurations for existing WhatsApp channels
    # through a data migration script
    
    # For now, this is a placeholder migration to track the change
    # The actual data will be migrated via a separate script
    pass


def downgrade() -> None:
    # Remove the configurations that were added
    # This will be handled by the data migration script
    pass
