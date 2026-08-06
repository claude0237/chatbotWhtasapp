"""add_ml_quotas_table

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-08-04 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'g7b8c9d0e1f2'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ml_quotas table using String for plan to avoid enum conflict
    op.create_table(
        'ml_quotas',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('plan', sa.String(length=20), nullable=False),
        sa.Column('monthly_requests', sa.Integer(), nullable=False),
        sa.Column('daily_requests', sa.Integer(), nullable=True),
        sa.Column('max_tokens_per_request', sa.Integer(), nullable=True),
        sa.Column('price_per_1000_requests', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plan')
    )
    op.create_index(op.f('ix_ml_quotas_id'), 'ml_quotas', ['id'], unique=False)
    op.create_index(op.f('ix_ml_quotas_plan'), 'ml_quotas', ['plan'], unique=False)
    
    # Insert default quotas for each plan
    op.execute("""
        INSERT INTO ml_quotas (id, plan, monthly_requests, daily_requests, max_tokens_per_request, price_per_1000_requests, created_at, updated_at)
        VALUES
            (gen_random_uuid(), 'FREE', 0, NULL, NULL, NULL, NOW(), NOW()),
            (gen_random_uuid(), 'BASIC', 1000, 50, 500, 50, NOW(), NOW()),
            (gen_random_uuid(), 'PREMIUM', 10000, 500, 1000, 30, NOW(), NOW()),
            (gen_random_uuid(), 'ENTERPRISE', -1, NULL, 2000, 20, NOW(), NOW())
    """)


def downgrade() -> None:
    op.drop_index(op.f('ix_ml_quotas_plan'), table_name='ml_quotas')
    op.drop_index(op.f('ix_ml_quotas_id'), table_name='ml_quotas')
    op.drop_table('ml_quotas')
