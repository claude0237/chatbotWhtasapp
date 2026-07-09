"""add_bot_followup_fields

Revision ID: a1b2c3d4e5f6
Revises: 27a1dd4d0ad8
Create Date: 2026-07-06 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '27a1dd4d0ad8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('bot_configurations',
        sa.Column('followup_timeout_minutes', sa.Integer(), nullable=False, server_default='60'))
    op.add_column('bot_configurations',
        sa.Column('followup_max_retries', sa.Integer(), nullable=False, server_default='3'))
    op.add_column('bot_conversation_states',
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('bot_conversation_states',
        sa.Column('last_bot_message', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('bot_conversation_states', 'last_bot_message')
    op.drop_column('bot_conversation_states', 'retry_count')
    op.drop_column('bot_configurations', 'followup_max_retries')
    op.drop_column('bot_configurations', 'followup_timeout_minutes')
