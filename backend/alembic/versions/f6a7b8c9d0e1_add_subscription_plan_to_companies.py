"""add_subscription_plan_to_companies

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-08-04 13:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type if not exists
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE subscriptionplan AS ENUM ('FREE', 'BASIC', 'PREMIUM', 'ENTERPRISE');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)
    
    # Add column with default value
    op.execute("""
        DO $$
        BEGIN
            ALTER TABLE companies ADD COLUMN subscription_plan subscriptionplan DEFAULT 'FREE' NOT NULL;
        EXCEPTION
            WHEN duplicate_column THEN NULL;
        END $$;
    """)


def downgrade() -> None:
    op.drop_column('companies', 'subscription_plan')
    
    # Drop enum type
    subscription_plan_enum = sa.Enum(name='subscriptionplan')
    subscription_plan_enum.drop(op.get_bind())
