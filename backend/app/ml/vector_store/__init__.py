"""Vector Store Service for managing embeddings and similarity search"""
from typing import List, Optional, Any
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.models import DocumentChunk
from app.ml.repositories import DocumentChunkRepository
from app.logging_config import log_with_context


class VectorStoreService:
    """Service for managing vector storage and similarity search using pgvector"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.chunk_repository = DocumentChunkRepository(db)
        self.logger = logging.getLogger("app.ml.vector_store")
    
    async def add_vectors(self, chunks: List[DocumentChunk]) -> bool:
        """Add vectors to the store"""
        try:
            await self.chunk_repository.create_batch(chunks)
            log_with_context(
                self.logger,
                logging.INFO,
                "VECTOR_STORE_ADD",
                count=len(chunks)
            )
            return True
        except Exception as e:
            log_with_context(
                self.logger,
                logging.ERROR,
                "VECTOR_STORE_ADD_FAILED",
                error_message=str(e),
                exc_info=True
            )
            return False
    
    async def search_similar(
        self,
        company_id: UUID,
        query_embedding: List[float],
        limit: int = 5,
        threshold: float = 0.5
    ) -> List[tuple[DocumentChunk, float]]:
        """Search for similar chunks using pgvector"""
        return await self.chunk_repository.search_similar(
            company_id=company_id,
            embedding=query_embedding,
            limit=limit,
            threshold=threshold
        )
    
    async def search_similar_by_text(
        self,
        company_id: UUID,
        query_text: str,
        embedding_service,
        limit: int = 5,
        threshold: float = 0.5
    ) -> List[tuple[DocumentChunk, float]]:
        """Search for similar chunks by text (generates embedding first)"""
        query_embedding = await embedding_service.embed_text(query_text)
        return await self.search_similar(
            company_id=company_id,
            query_embedding=query_embedding,
            limit=limit,
            threshold=threshold
        )
    
    async def delete_vectors(self, company_id: UUID, source_type: str, source_id: UUID) -> bool:
        """Delete all vectors for a source"""
        from app.ml.models import SourceType
        try:
            await self.chunk_repository.delete_by_source(
                company_id=company_id,
                source_type=SourceType(source_type),
                source_id=source_id
            )
            return True
        except Exception as e:
            log_with_context(
                self.logger,
                logging.ERROR,
                "VECTOR_STORE_DELETE_FAILED",
                error_message=str(e),
                exc_info=True
            )
            return False
    
    async def get_vector_count(self, company_id: UUID) -> int:
        """Get count of vectors for a company"""
        from sqlalchemy import text
        result = await self.db.execute(
            text("SELECT COUNT(*) FROM document_chunks WHERE company_id = :company_id"),
            {"company_id": str(company_id)}
        )
        return result.scalar()
