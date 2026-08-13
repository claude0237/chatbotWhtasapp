"""Knowledge Service"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.knowledge.models import KnowledgeBase, KnowledgeCategory, SourceType
from app.knowledge.repositories import KnowledgeBaseRepository, KnowledgeCategoryRepository
from app.ml.models import DocumentChunk, SourceType as VectorSourceType
from app.ml.embeddings import get_embedding_provider, EmbeddingService
from app.ml.repositories import DocumentChunkRepository


class KnowledgeBaseService:
    """Service for KnowledgeBase operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = KnowledgeBaseRepository(db)
        self.chunk_repository = DocumentChunkRepository(db)
        self.logger = logging.getLogger("app.knowledge")
    
    async def _sync_vector(self, entry: KnowledgeBase) -> None:
        """Sync a knowledge base entry with the vector store"""
        if not entry.is_active:
            await self.chunk_repository.delete_by_source(
                company_id=entry.company_id,
                source_type=VectorSourceType.KNOWLEDGE_BASE,
                source_id=entry.id
            )
            return
        
        # Combine title and content for embedding
        text_to_embed = f"{entry.title}\n\n{entry.content}"
        
        # Generate embedding
        provider = get_embedding_provider("local")
        embedding_service = EmbeddingService(provider)
        embedding = await embedding_service.embed_text(text_to_embed)
        
        # Delete existing chunk for this entry
        existing = await self.chunk_repository.get_by_source(
            company_id=entry.company_id,
            source_type=VectorSourceType.KNOWLEDGE_BASE,
            source_id=entry.id
        )
        if existing:
            await self.db.delete(existing)
        
        # Create new chunk
        chunk = DocumentChunk(
            company_id=entry.company_id,
            document_id=None,
            content=entry.content,
            chunk_index=0,
            source_type=VectorSourceType.KNOWLEDGE_BASE,
            source_id=entry.id,
            embedding=embedding,
            extra_data={"title": entry.title, "source": "knowledge_base"}
        )
        self.db.add(chunk)
        await self.db.commit()
    
    async def create_entry(
        self,
        company_id: UUID,
        title: str,
        content: str,
        category_id: Optional[UUID] = None,
        source_type: SourceType = SourceType.MANUAL,
        source_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgeBase:
        """Create a new knowledge base entry"""
        entry = KnowledgeBase(
            company_id=company_id,
            title=title,
            content=content,
            category_id=category_id,
            source_type=source_type,
            source_id=source_id,
            extra_data=metadata,
            version=1,
            is_active=True
        )
        entry = await self.repository.create(entry)
        
        # Sync with vector store
        try:
            await self._sync_vector(entry)
        except Exception as e:
            self.logger.error(f"Failed to sync knowledge base vector: {str(e)}", exc_info=True)
        
        return entry
    
    async def update_entry(
        self,
        entry_id: UUID,
        title: Optional[str] = None,
        content: Optional[str] = None,
        category_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None
    ) -> Optional[KnowledgeBase]:
        """Update knowledge base entry"""
        entry = await self.repository.get_by_id(entry_id)
        if entry:
            if title is not None:
                entry.title = title
            if content is not None:
                entry.content = content
            if category_id is not None:
                entry.category_id = category_id
            if metadata is not None:
                entry.extra_data = metadata
            if is_active is not None:
                entry.is_active = is_active
            entry.version += 1
            entry = await self.repository.update(entry)
            
            # Sync with vector store
            try:
                await self._sync_vector(entry)
            except Exception as e:
                self.logger.error(f"Failed to sync knowledge base vector: {str(e)}", exc_info=True)
            
            return entry
        return None
    
    async def delete_entry(self, entry_id: UUID) -> bool:
        """Delete knowledge base entry"""
        entry = await self.repository.get_by_id(entry_id)
        if entry:
            # Delete from vector store
            try:
                await self.chunk_repository.delete_by_source(
                    company_id=entry.company_id,
                    source_type=VectorSourceType.KNOWLEDGE_BASE,
                    source_id=entry.id
                )
            except Exception as e:
                self.logger.error(f"Failed to delete knowledge base vector: {str(e)}", exc_info=True)
            
            return await self.repository.delete(entry_id)
        return False
    
    async def search(self, company_id: UUID, query: str, skip: int = 0, limit: int = 100) -> List[KnowledgeBase]:
        """Search knowledge base entries"""
        return await self.repository.search(company_id, query, skip, limit)
    
    async def get_by_category(self, category_id: UUID, skip: int = 0, limit: int = 100) -> List[KnowledgeBase]:
        """Get knowledge base entries by category"""
        return await self.repository.get_by_category_id(category_id, skip, limit)
    
    async def get_by_id(self, entry_id: UUID) -> Optional[KnowledgeBase]:
        """Get knowledge base entry by ID"""
        return await self.repository.get_by_id(entry_id)
    
    async def get_by_company_id(self, company_id: UUID, skip: int = 0, limit: int = 100) -> List[KnowledgeBase]:
        """Get knowledge base entries by company ID"""
        return await self.repository.get_by_company_id(company_id, skip, limit)
    
    async def get_active_entries(self, company_id: UUID, skip: int = 0, limit: int = 100) -> List[KnowledgeBase]:
        """Get active knowledge base entries"""
        return await self.repository.get_active_entries(company_id, skip, limit)


class KnowledgeCategoryService:
    """Service for KnowledgeCategory operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = KnowledgeCategoryRepository(db)
    
    async def create_category(
        self,
        company_id: UUID,
        name: str,
        parent_id: Optional[UUID] = None,
        icon: Optional[str] = None
    ) -> KnowledgeCategory:
        """Create a new knowledge category"""
        category = KnowledgeCategory(
            company_id=company_id,
            name=name,
            parent_id=parent_id,
            icon=icon
        )
        return await self.repository.create(category)
    
    async def update_category(
        self,
        category_id: UUID,
        name: Optional[str] = None,
        parent_id: Optional[UUID] = None,
        icon: Optional[str] = None
    ) -> Optional[KnowledgeCategory]:
        """Update knowledge category"""
        category = await self.repository.get_by_id(category_id)
        if category:
            if name is not None:
                category.name = name
            if parent_id is not None:
                category.parent_id = parent_id
            if icon is not None:
                category.icon = icon
            return await self.repository.update(category)
        return None
    
    async def delete_category(self, category_id: UUID) -> bool:
        """Delete knowledge category"""
        return await self.repository.delete(category_id)
    
    async def get_by_id(self, category_id: UUID) -> Optional[KnowledgeCategory]:
        """Get knowledge category by ID"""
        return await self.repository.get_by_id(category_id)
    
    async def get_by_company_id(self, company_id: UUID, skip: int = 0, limit: int = 100) -> List[KnowledgeCategory]:
        """Get knowledge categories by company ID"""
        return await self.repository.get_by_company_id(company_id, skip, limit)
    
    async def get_root_categories(self, company_id: UUID) -> List[KnowledgeCategory]:
        """Get root categories for a company"""
        return await self.repository.get_root_categories(company_id)
    
    async def get_children(self, parent_id: UUID) -> List[KnowledgeCategory]:
        """Get child categories for a parent"""
        return await self.repository.get_children(parent_id)
