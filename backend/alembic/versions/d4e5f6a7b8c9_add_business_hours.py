"""add_business_hours

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-07 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            ALTER TABLE bot_configurations ADD COLUMN IF NOT EXISTS business_hours JSON;
        EXCEPTION
            WHEN duplicate_column THEN NULL;
        END $$;
    """)


def downgrade() -> None:
    op.drop_column('bot_configurations', 'business_hours')
