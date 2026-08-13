"""ML Service - Knowledge Ingestion Pipeline"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.models import Document, DocumentChunk, IngestionJob, FileType, DocumentStatus, IngestionJobStatus, SourceType
from app.ml.repositories import DocumentRepository, DocumentChunkRepository, IngestionJobRepository
from app.ml.extractors import get_extractor, TextChunker
from app.ml.embeddings import get_embedding_provider, get_redis_client, EmbeddingService


class KnowledgeIngestionService:
    """Service for ingesting documents and generating embeddings"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.document_repository = DocumentRepository(db)
        self.chunk_repository = DocumentChunkRepository(db)
        self.job_repository = IngestionJobRepository(db)
        self.chunker = TextChunker(chunk_size=1000, chunk_overlap=200)
        
        # Initialize embedding service (Redis client will be initialized lazily)
        provider = get_embedding_provider(provider_type="local")  # Default to local
        self.embedding_service = EmbeddingService(provider, redis_client=None)
        self._redis_client = None
    
    async def _ensure_redis_client(self):
        """Lazily initialize Redis client"""
        if self._redis_client is None:
            self._redis_client = await get_redis_client()
            self.embedding_service.redis_client = self._redis_client
    
    async def ingest_document(
        self,
        company_id: UUID,
        file_name: str,
        file_type: FileType,
        file_path: str,
        file_size: Optional[int] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Document:
        """Ingest a single document"""
        await self._ensure_redis_client()
        # Create document record
        document = Document(
            company_id=company_id,
            file_name=file_name,
            file_type=file_type,
            file_path=file_path,
            file_size=file_size,
            status=DocumentStatus.PROCESSING,
            chunk_count=0,
            extra_data=extra_data
        )
        document = await self.document_repository.create(document)
        
        try:
            # Extract text
            extractor = get_extractor(file_type.value)
            text = await extractor.extract_text(file_path)
            
            # Extract metadata
            metadata = await extractor.extract_metadata(file_path)
            if metadata:
                document.extra_data = {**(extra_data or {}), **metadata}
                document = await self.document_repository.update(document)
            
            # Chunk text
            chunks = self.chunker.chunk(text, method="paragraph")
            
            # Generate embeddings for chunks
            embeddings = await self.embedding_service.embed_document_chunks(chunks)
            
            # Create chunk records
            chunk_records = []
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_record = DocumentChunk(
                    company_id=document.company_id,
                    document_id=document.id,
                    source_type=SourceType.DOCUMENT,
                    source_id=document.id,
                    content=chunk,
                    chunk_index=idx,
                    embedding=embedding
                )
                chunk_records.append(chunk_record)
            
            await self.chunk_repository.create_batch(chunk_records)
            
            # Update document status
            document.status = DocumentStatus.COMPLETED
            document.chunk_count = len(chunk_records)
            document.processed_at = datetime.utcnow()
            document = await self.document_repository.update(document)
            
        except Exception as e:
            # Update document status to failed
            document.status = DocumentStatus.FAILED
            document.extra_data = {**(document.extra_data or {}), "error": str(e)}
            document = await self.document_repository.update(document)
            raise
        
        return document
    
    async def ingest_from_database(
        self,
        company_id: UUID,
        source_config: Dict[str, Any]
    ) -> IngestionJob:
        """Ingest documents from database (e.g., knowledge base entries)"""
        await self._ensure_redis_client()
        # Create ingestion job
        job = IngestionJob(
            company_id=company_id,
            source_type="DATABASE",
            source_config=source_config,
            status=IngestionJobStatus.RUNNING,
            started_at=datetime.utcnow(),
            total_documents=0,
            processed_documents=0,
            failed_documents=0
        )
        job = await self.job_repository.create(job)
        
        try:
            # Import here to avoid circular dependency
            from app.knowledge.repositories import KnowledgeBaseRepository
            kb_repository = KnowledgeBaseRepository(self.db)
            
            # Get knowledge base entries
            entries = await kb_repository.get_active_entries(company_id)
            job.total_documents = len(entries)
            job = await self.job_repository.update(job)
            
            # Process each entry as a document
            for entry in entries:
                try:
                    # Create a virtual document for the knowledge entry
                    document = Document(
                        company_id=company_id,
                        file_name=f"kb_entry_{entry.id}",
                        file_type=FileType.TXT,
                        file_path=None,  # Virtual document
                        status=DocumentStatus.PROCESSING,
                        chunk_count=0,
                        extra_data={"source": "knowledge_base", "entry_id": str(entry.id)}
                    )
                    document = await self.document_repository.create(document)
                    
                    # Chunk the content
                    chunks = self.chunker.chunk(entry.content, method="paragraph")
                    
                    # Generate embeddings
                    embeddings = await self.embedding_service.embed_document_chunks(chunks)
                    
                    # Create chunk records
                    chunk_records = []
                    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                        chunk_record = DocumentChunk(
                            company_id=document.company_id,
                            document_id=document.id,
                            source_type=SourceType.DOCUMENT,
                            source_id=document.id,
                            content=chunk,
                            chunk_index=idx,
                            embedding=embedding
                        )
                        chunk_records.append(chunk_record)
                    
                    await self.chunk_repository.create_batch(chunk_records)
                    
                    # Update document status
                    document.status = DocumentStatus.COMPLETED
                    document.chunk_count = len(chunk_records)
                    document.processed_at = datetime.utcnow()
                    document = await self.document_repository.update(document)
                    
                    job.processed_documents += 1
                    job = await self.job_repository.update(job)
                    
                except Exception as e:
                    job.failed_documents += 1
                    job = await self.job_repository.update(job)
                    print(f"Failed to process entry {entry.id}: {str(e)}")
            
            # Update job status
            job.status = IngestionJobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job = await self.job_repository.update(job)
            
        except Exception as e:
            job.status = IngestionJobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            job = await self.job_repository.update(job)
            raise
        
        return job
    
    async def reindex_all(self, company_id: UUID) -> IngestionJob:
        """Reindex all documents for a company"""
        await self._ensure_redis_client()
        # Create ingestion job
        job = IngestionJob(
            company_id=company_id,
            source_type="REINDEX",
            source_config={},
            status=IngestionJobStatus.RUNNING,
            started_at=datetime.utcnow(),
            total_documents=0,
            processed_documents=0,
            failed_documents=0
        )
        job = await self.job_repository.create(job)
        
        try:
            # Get all documents
            documents = await self.document_repository.get_by_company_id(company_id)
            job.total_documents = len(documents)
            job = await self.job_repository.update(job)
            
            # Process each document
            for document in documents:
                try:
                    # Delete existing chunks
                    await self.chunk_repository.delete_by_document_id(document.id)
                    
                    # Re-extract text if file_path exists
                    if document.file_path:
                        extractor = get_extractor(document.file_type.value)
                        text = await extractor.extract_text(document.file_path)
                    else:
                        # Skip virtual documents without file_path
                        job.processed_documents += 1
                        job = await self.job_repository.update(job)
                        continue
                    
                    # Chunk text
                    chunks = self.chunker.chunk(text, method="paragraph")
                    
                    # Generate embeddings
                    embeddings = await self.embedding_service.embed_document_chunks(chunks)
                    
                    # Create chunk records
                    chunk_records = []
                    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                        chunk_record = DocumentChunk(
                            company_id=document.company_id,
                            document_id=document.id,
                            source_type=SourceType.DOCUMENT,
                            source_id=document.id,
                            content=chunk,
                            chunk_index=idx,
                            embedding=embedding
                        )
                        chunk_records.append(chunk_record)
                    
                    await self.chunk_repository.create_batch(chunk_records)
                    
                    # Update document status
                    document.status = DocumentStatus.COMPLETED
                    document.chunk_count = len(chunk_records)
                    document.processed_at = datetime.utcnow()
                    document = await self.document_repository.update(document)
                    
                    job.processed_documents += 1
                    job = await self.job_repository.update(job)
                    
                except Exception as e:
                    job.failed_documents += 1
                    job = await self.job_repository.update(job)
                    print(f"Failed to reindex document {document.id}: {str(e)}")
            
            # Update job status
            job.status = IngestionJobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job = await self.job_repository.update(job)
            
        except Exception as e:
            job.status = IngestionJobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            job = await self.job_repository.update(job)
            raise
        
        return job
    
    async def delete_document(self, document_id: UUID) -> bool:
        """Delete a document and its chunks"""
        # Delete chunks first
        await self.chunk_repository.delete_by_document_id(document_id)
        
        # Delete document
        return await self.document_repository.delete(document_id)
    
    async def search_similar_chunks(
        self,
        company_id: UUID,
        query: str,
        limit: int = 5
    ) -> List[DocumentChunk]:
        """Search for similar chunks using embedding similarity"""
        await self._ensure_redis_client()
        # Generate query embedding
        query_embedding = await self.embedding_service.embed_text(query)
        
        # Get all chunks with embeddings for the company
        chunks = await self.chunk_repository.get_chunks_with_embeddings(company_id, limit=100)
        
        # Calculate cosine similarity
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        
        similarities = []
        for chunk in chunks:
            if chunk.embedding:
                chunk_embedding = np.array(chunk.embedding).reshape(1, -1)
                query_embedding_np = np.array(query_embedding).reshape(1, -1)
                similarity = cosine_similarity(chunk_embedding, query_embedding_np)[0][0]
                similarities.append((chunk, similarity))
        
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [chunk for chunk, _ in similarities[:limit]]
