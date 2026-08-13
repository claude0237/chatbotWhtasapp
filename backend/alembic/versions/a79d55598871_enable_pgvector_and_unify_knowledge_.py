"""enable pgvector and unify knowledge base vectors

Revision ID: a79d55598871
Revises: merge1
Create Date: 2026-08-13 18:23:58.032604

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'a79d55598871'
down_revision: Union[str, Sequence[str], None] = 'merge1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Add company_id, source_type and source_id columns to document_chunks
    op.add_column('document_chunks', sa.Column('company_id', sa.UUID(), nullable=True))
    op.add_column('document_chunks', sa.Column('source_type', sa.String(length=50), nullable=True))
    op.add_column('document_chunks', sa.Column('source_id', sa.UUID(), nullable=True))

    # Make document_id nullable to support knowledge base chunks without a document
    op.alter_column('document_chunks', 'document_id', nullable=True)

    # Backfill existing document chunks with company_id and source metadata
    op.execute("""
        UPDATE document_chunks dc
        SET company_id = d.company_id,
            source_type = 'DOCUMENT',
            source_id = dc.document_id
        FROM documents d
        WHERE dc.document_id = d.id
    """)

    # Make company_id non-nullable after backfill
    op.alter_column('document_chunks', 'company_id', nullable=False)

    # Add foreign key for company_id
    op.create_foreign_key(
        'fk_document_chunks_company_id_companies',
        'document_chunks', 'companies',
        ['company_id'], ['id'],
        ondelete='CASCADE'
    )

    # Drop old JSON embedding column and add pgvector Vector column (384 dims for all-MiniLM-L6-v2)
    op.drop_column('document_chunks', 'embedding')
    op.add_column('document_chunks', sa.Column('embedding', Vector(384), nullable=True))

    # Create indexes
    op.create_index(op.f('ix_document_chunks_company_id'), 'document_chunks', ['company_id'], unique=False)
    op.create_index(op.f('ix_document_chunks_source_type'), 'document_chunks', ['source_type'], unique=False)
    op.create_index(
        op.f('ix_document_chunks_embedding'),
        'document_chunks',
        ['embedding'],
        unique=False,
        postgresql_using='ivfflat'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index(op.f('ix_document_chunks_embedding'), table_name='document_chunks')
    op.drop_index(op.f('ix_document_chunks_source_type'), table_name='document_chunks')
    op.drop_index(op.f('ix_document_chunks_company_id'), table_name='document_chunks')

    # Drop foreign key
    op.drop_constraint('fk_document_chunks_company_id_companies', 'document_chunks')

    # Restore JSON embedding column
    op.drop_column('document_chunks', 'embedding')
    op.add_column('document_chunks', sa.Column('embedding', sa.JSON(), nullable=True))

    # Drop added columns
    op.drop_column('document_chunks', 'source_id')
    op.drop_column('document_chunks', 'source_type')
    op.drop_column('document_chunks', 'company_id')

    # Drop pgvector extension
    op.execute("DROP EXTENSION IF EXISTS vector")
