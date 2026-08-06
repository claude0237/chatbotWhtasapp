"""add_ml_usage_table

Revision ID: h8c9d0e1f2g3
Revises: g7b8c9d0e1f2
Create Date: 2026-08-04 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'h8c9d0e1f2g3'
down_revision: Union[str, None] = 'g7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ml_usage',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('monthly_requests', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('daily_requests', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_requests', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_month', sa.Integer(), nullable=False),
        sa.Column('current_day', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ml_usage_id'), 'ml_usage', ['id'], unique=False)
    op.create_index(op.f('ix_ml_usage_company_id'), 'ml_usage', ['company_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ml_usage_company_id'), table_name='ml_usage')
    op.drop_index(op.f('ix_ml_usage_id'), table_name='ml_usage')
    op.drop_table('ml_usage')
