"""Knowledge Repository"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.knowledge.models import KnowledgeBase, KnowledgeCategory, SourceType


class KnowledgeBaseRepository:
    """Repository for KnowledgeBase model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, entry: KnowledgeBase) -> KnowledgeBase:
        """Create a new knowledge base entry"""
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry
    
    async def get_by_id(self, entry_id: UUID) -> Optional[KnowledgeBase]:
        """Get knowledge base entry by ID"""
        result = await self.db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == entry_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_company_id(self, company_id: UUID, skip: int = 0, limit: int = 100) -> List[KnowledgeBase]:
        """Get knowledge base entries by company ID with pagination"""
        result = await self.db.execute(
            select(KnowledgeBase)
            .where(KnowledgeBase.company_id == company_id)
            .order_by(KnowledgeBase.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_category_id(self, category_id: UUID, skip: int = 0, limit: int = 100) -> List[KnowledgeBase]:
        """Get knowledge base entries by category ID with pagination"""
        result = await self.db.execute(
            select(KnowledgeBase)
            .where(KnowledgeBase.category_id == category_id)
            .order_by(KnowledgeBase.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_active_entries(self, company_id: UUID, skip: int = 0, limit: int = 100) -> List[KnowledgeBase]:
        """Get active knowledge base entries for a company"""
        result = await self.db.execute(
            select(KnowledgeBase)
            .where(
                and_(
                    KnowledgeBase.company_id == company_id,
                    KnowledgeBase.is_active == True
                )
            )
            .order_by(KnowledgeBase.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def search(self, company_id: UUID, query: str, skip: int = 0, limit: int = 100) -> List[KnowledgeBase]:
        """Search knowledge base entries by title or content"""
        search_pattern = f"%{query}%"
        result = await self.db.execute(
            select(KnowledgeBase)
            .where(
                and_(
                    KnowledgeBase.company_id == company_id,
                    KnowledgeBase.is_active == True,
                    or_(
                        KnowledgeBase.title.ilike(search_pattern),
                        KnowledgeBase.content.ilike(search_pattern)
                    )
                )
            )
            .order_by(KnowledgeBase.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def update(self, entry: KnowledgeBase) -> KnowledgeBase:
        """Update knowledge base entry"""
        await self.db.commit()
        await self.db.refresh(entry)
        return entry
    
    async def delete(self, entry_id: UUID) -> bool:
        """Delete knowledge base entry by ID"""
        entry = await self.get_by_id(entry_id)
        if entry:
            await self.db.delete(entry)
            await self.db.commit()
            return True
        return False


class KnowledgeCategoryRepository:
    """Repository for KnowledgeCategory model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, category: KnowledgeCategory) -> KnowledgeCategory:
        """Create a new knowledge category"""
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category
    
    async def get_by_id(self, category_id: UUID) -> Optional[KnowledgeCategory]:
        """Get knowledge category by ID"""
        result = await self.db.execute(
            select(KnowledgeCategory).where(KnowledgeCategory.id == category_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_company_id(self, company_id: UUID, skip: int = 0, limit: int = 100) -> List[KnowledgeCategory]:
        """Get knowledge categories by company ID with pagination"""
        result = await self.db.execute(
            select(KnowledgeCategory)
            .where(KnowledgeCategory.company_id == company_id)
            .order_by(KnowledgeCategory.name.asc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_root_categories(self, company_id: UUID) -> List[KnowledgeCategory]:
        """Get root categories (no parent) for a company"""
        result = await self.db.execute(
            select(KnowledgeCategory)
            .where(
                and_(
                    KnowledgeCategory.company_id == company_id,
                    KnowledgeCategory.parent_id.is_(None)
                )
            )
            .order_by(KnowledgeCategory.name.asc())
        )
        return result.scalars().all()
    
    async def get_children(self, parent_id: UUID) -> List[KnowledgeCategory]:
        """Get child categories for a parent category"""
        result = await self.db.execute(
            select(KnowledgeCategory)
            .where(KnowledgeCategory.parent_id == parent_id)
            .order_by(KnowledgeCategory.name.asc())
        )
        return result.scalars().all()
    
    async def update(self, category: KnowledgeCategory) -> KnowledgeCategory:
        """Update knowledge category"""
        await self.db.commit()
        await self.db.refresh(category)
        return category
    
    async def delete(self, category_id: UUID) -> bool:
        """Delete knowledge category by ID"""
        category = await self.get_by_id(category_id)
        if category:
            await self.db.delete(category)
            await self.db.commit()
            return True
        return False
