"""Vector Store Service for managing embeddings and similarity search"""
from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.ml.models import DocumentChunk
from app.ml.repositories import DocumentChunkRepository


class VectorStoreService:
    """Service for managing vector storage and similarity search"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.chunk_repository = DocumentChunkRepository(db)
    
    async def add_vectors(self, chunks: List[DocumentChunk]) -> bool:
        """Add vectors to the store"""
        try:
            await self.chunk_repository.create_batch(chunks)
            return True
        except Exception as e:
            print(f"Error adding vectors: {str(e)}")
            return False
    
    async def search_similar(
        self,
        company_id: UUID,
        query_embedding: List[float],
        limit: int = 5,
        threshold: float = 0.5
    ) -> List[tuple[DocumentChunk, float]]:
        """Search for similar chunks using sklearn cosine similarity (pgvector disabled for now)"""
        # Directly use sklearn fallback due to pgvector syntax issues
        return await self._search_similar_sklearn(company_id, query_embedding, limit, threshold)
    
    async def _search_similar_sklearn(
        self,
        company_id: UUID,
        query_embedding: List[float],
        limit: int = 5,
        threshold: float = 0.5
    ) -> List[tuple[DocumentChunk, float]]:
        """Fallback search using sklearn cosine similarity"""
        # Get all chunks with embeddings for the company
        chunks = await self.chunk_repository.get_chunks_with_embeddings(company_id, limit=100)
        
        if not chunks:
            return []
        
        # Calculate cosine similarity
        similarities = []
        query_embedding_np = np.array(query_embedding).reshape(1, -1)
        
        for chunk in chunks:
            if chunk.embedding and len(chunk.embedding) > 0:
                chunk_embedding_np = np.array(chunk.embedding).reshape(1, -1)
                similarity = cosine_similarity(chunk_embedding_np, query_embedding_np)[0][0]
                if similarity >= threshold:
                    similarities.append((chunk, similarity))
        
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]
    
    async def search_similar_by_text(
        self,
        company_id: UUID,
        query_text: str,
        embedding_service,
        limit: int = 5,
        threshold: float = 0.5
    ) -> List[tuple[DocumentChunk, float]]:
        """Search for similar chunks by text (generates embedding first)"""
        # Generate query embedding
        query_embedding = await embedding_service.embed_text(query_text)
        return await self.search_similar(company_id, query_embedding, limit, threshold)
    
    async def delete_vectors(self, document_id: UUID) -> bool:
        """Delete all vectors for a document"""
        try:
            await self.chunk_repository.delete_by_document_id(document_id)
            return True
        except Exception as e:
            print(f"Error deleting vectors: {str(e)}")
            return False
    
    async def get_vector_count(self, company_id: UUID) -> int:
        """Get count of vectors for a company"""
        chunks = await self.chunk_repository.get_chunks_with_embeddings(company_id, limit=10000)
        return len(chunks)
