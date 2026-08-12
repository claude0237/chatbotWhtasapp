"""Add ML provider configs table

Revision ID: j0k1l2m3n4o5
Revises: i9d0e1f2g3h4
Create Date: 2026-08-10 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'j0k1l2m3n4o5'
down_revision: Union[str, None] = 'i9d0e1f2g3h4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ml_provider_configs table
    op.create_table(
        'ml_provider_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('provider_type', sa.Enum('OPENAI', 'MISTRAL', 'ANTHROPIC', name='mlprovidertype'), nullable=False, unique=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('api_key', sa.String(500), nullable=True),
        sa.Column('api_endpoint', sa.String(500), nullable=True),
        sa.Column('default_model', sa.String(200), nullable=True),
        sa.Column('default_temperature', sa.Integer(), nullable=True),
        sa.Column('default_max_tokens', sa.Integer(), nullable=True),
        sa.Column('requests_per_minute', sa.Integer(), nullable=True),
        sa.Column('requests_per_day', sa.Integer(), nullable=True),
        sa.Column('extra_config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('ml_provider_configs')
