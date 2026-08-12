"""Company Repository"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.companies.models import Company, CompanySettings


class CompanyRepository:
    """Repository for Company model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, company: Company) -> Company:
        """Create a new company"""
        self.db.add(company)
        await self.db.commit()
        await self.db.refresh(company)
        return company
    
    async def get_by_id(self, company_id: UUID) -> Optional[Company]:
        """Get company by ID"""
        result = await self.db.execute(
            select(Company).where(Company.id == company_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_slug(self, slug: str) -> Optional[Company]:
        """Get company by slug"""
        result = await self.db.execute(
            select(Company).where(Company.slug == slug)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Company]:
        """Get all companies with pagination (excluding soft-deleted)"""
        result = await self.db.execute(
            select(Company).where(Company.deleted_at == None).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def update(self, company: Company) -> Company:
        """Update company"""
        await self.db.commit()
        await self.db.refresh(company)
        return company
    
    async def delete(self, company_id: UUID) -> bool:
        """Delete company by ID (hard delete — cascades to users, conversations, etc.)"""
        company = await self.get_by_id(company_id)
        if company:
            await self.db.delete(company)
            await self.db.commit()
            return True
        return False
    
    async def get_active_companies(self) -> List[Company]:
        """Get all active companies"""
        result = await self.db.execute(
            select(Company).where(Company.is_active == True)
        )
        return result.scalars().all()


class CompanySettingsRepository:
    """Repository for CompanySettings model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, settings: CompanySettings) -> CompanySettings:
        """Create company settings"""
        self.db.add(settings)
        await self.db.commit()
        await self.db.refresh(settings)
        return settings
    
    async def get_by_company_id(self, company_id: UUID) -> Optional[CompanySettings]:
        """Get settings by company ID"""
        result = await self.db.execute(
            select(CompanySettings).where(CompanySettings.company_id == company_id)
        )
        return result.scalar_one_or_none()
    
    async def update(self, settings: CompanySettings) -> CompanySettings:
        """Update company settings"""
        await self.db.commit()
        await self.db.refresh(settings)
        return settings
