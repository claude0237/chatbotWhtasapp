"""ML Repository"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.ml.models import Document, DocumentChunk, IngestionJob, DocumentStatus, IngestionJobStatus


class DocumentRepository:
    """Repository for Document model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, document: Document) -> Document:
        """Create a new document"""
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        return document
    
    async def get_by_id(self, document_id: UUID) -> Optional[Document]:
        """Get document by ID"""
        result = await self.db.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_company_id(self, company_id: UUID, skip: int = 0, limit: int = 100) -> List[Document]:
        """Get documents by company ID with pagination"""
        result = await self.db.execute(
            select(Document)
            .where(Document.company_id == company_id)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_status(self, company_id: UUID, status: DocumentStatus, skip: int = 0, limit: int = 100) -> List[Document]:
        """Get documents by status for a company"""
        result = await self.db.execute(
            select(Document)
            .where(
                and_(
                    Document.company_id == company_id,
                    Document.status == status
                )
            )
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def update(self, document: Document) -> Document:
        """Update document"""
        await self.db.commit()
        await self.db.refresh(document)
        return document
    
    async def delete(self, document_id: UUID) -> bool:
        """Delete document by ID"""
        document = await self.get_by_id(document_id)
        if document:
            await self.db.delete(document)
            await self.db.commit()
            return True
        return False


class DocumentChunkRepository:
    """Repository for DocumentChunk model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, chunk: DocumentChunk) -> DocumentChunk:
        """Create a new document chunk"""
        self.db.add(chunk)
        await self.db.commit()
        await self.db.refresh(chunk)
        return chunk
    
    async def create_batch(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Create multiple document chunks"""
        self.db.add_all(chunks)
        await self.db.commit()
        for chunk in chunks:
            await self.db.refresh(chunk)
        return chunks
    
    async def get_by_id(self, chunk_id: UUID) -> Optional[DocumentChunk]:
        """Get chunk by ID"""
        result = await self.db.execute(
            select(DocumentChunk).where(DocumentChunk.id == chunk_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_document_id(self, document_id: UUID) -> List[DocumentChunk]:
        """Get chunks by document ID"""
        result = await self.db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
        )
        return result.scalars().all()
    
    async def get_chunks_with_embeddings(self, company_id: UUID, limit: int = 100) -> List[DocumentChunk]:
        """Get chunks with embeddings for a company"""
        result = await self.db.execute(
            select(DocumentChunk)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(
                and_(
                    Document.company_id == company_id,
                    DocumentChunk.embedding.isnot(None)
                )
            )
            .order_by(DocumentChunk.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def update(self, chunk: DocumentChunk) -> DocumentChunk:
        """Update chunk"""
        await self.db.commit()
        await self.db.refresh(chunk)
        return chunk
    
    async def delete_by_document_id(self, document_id: UUID) -> bool:
        """Delete all chunks for a document"""
        chunks = await self.get_by_document_id(document_id)
        for chunk in chunks:
            await self.db.delete(chunk)
        await self.db.commit()
        return True


class IngestionJobRepository:
    """Repository for IngestionJob model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, job: IngestionJob) -> IngestionJob:
        """Create a new ingestion job"""
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job
    
    async def get_by_id(self, job_id: UUID) -> Optional[IngestionJob]:
        """Get job by ID"""
        result = await self.db.execute(
            select(IngestionJob).where(IngestionJob.id == job_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_company_id(self, company_id: UUID, skip: int = 0, limit: int = 100) -> List[IngestionJob]:
        """Get jobs by company ID with pagination"""
        result = await self.db.execute(
            select(IngestionJob)
            .where(IngestionJob.company_id == company_id)
            .order_by(IngestionJob.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_status(self, company_id: UUID, status: IngestionJobStatus) -> List[IngestionJob]:
        """Get jobs by status for a company"""
        result = await self.db.execute(
            select(IngestionJob)
            .where(
                and_(
                    IngestionJob.company_id == company_id,
                    IngestionJob.status == status
                )
            )
            .order_by(IngestionJob.created_at.desc())
        )
        return result.scalars().all()
    
    async def update(self, job: IngestionJob) -> IngestionJob:
        """Update job"""
        await self.db.commit()
        await self.db.refresh(job)
        return job
    
    async def delete(self, job_id: UUID) -> bool:
        """Delete job by ID"""
        job = await self.get_by_id(job_id)
        if job:
            await self.db.delete(job)
            await self.db.commit()
            return True
        return False
