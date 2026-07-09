"""Vector Store Service for managing embeddings and similarity search"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, text
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
        """Search for similar chunks using pgvector cosine similarity"""
        try:
            # Use pgvector for efficient similarity search
            # Convert embedding to PostgreSQL array format
            embedding_array = '[' + ','.join(map(str, query_embedding)) + ']'
            
            # Use pgvector's cosine distance (1 - cosine similarity)
            query = text("""
                SELECT dc.id, dc.document_id, dc.content, dc.chunk_index, 
                       dc.embedding, dc.extra_data, dc.created_at, dc.updated_at,
                       1 - (embedding <=> :query_embedding::vector) as similarity
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE d.company_id = :company_id
                  AND dc.embedding IS NOT NULL
                  AND (1 - (embedding <=> :query_embedding::vector)) >= :threshold
                ORDER BY similarity DESC
                LIMIT :limit
            """)
            
            result = await self.db.execute(
                query,
                {
                    "query_embedding": embedding_array,
                    "company_id": str(company_id),
                    "threshold": threshold,
                    "limit": limit
                }
            )
            
            rows = result.fetchall()
            
            # Convert rows to DocumentChunk objects with similarity scores
            similarities = []
            for row in rows:
                chunk = DocumentChunk(
                    id=row[0],
                    document_id=row[1],
                    content=row[2],
                    chunk_index=row[3],
                    embedding=row[4],
                    extra_data=row[5],
                    created_at=row[6],
                    updated_at=row[7]
                )
                similarity = float(row[8])
                similarities.append((chunk, similarity))
            
            return similarities
        except Exception as e:
            print(f"pgvector search failed, falling back to sklearn: {str(e)}")
            # Fallback to sklearn cosine similarity
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
