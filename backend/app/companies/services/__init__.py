"""Company Service"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.companies.models import Company, CompanySettings
from app.companies.repositories import CompanyRepository, CompanySettingsRepository
from app.companies.schemas import CompanyCreate, CompanyUpdate, CompanySettingsCreate, CompanySettingsUpdate


class CompanyService:
    """Service for company operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.company_repository = CompanyRepository(db)
        self.settings_repository = CompanySettingsRepository(db)
    
    async def create_company(self, company_data: CompanyCreate) -> Company:
        """Create a new company and its settings"""
        company = Company(
            name=company_data.name,
            slug=company_data.slug,
            description=company_data.description,
            logo_url=company_data.logo_url,
            website=company_data.website,
            email=company_data.email,
            phone=company_data.phone,
            address=company_data.address,
            is_active=company_data.is_active,
            is_suspended=company_data.is_suspended,
        )
        company = await self.company_repository.create(company)

        # Auto-create company settings
        settings = CompanySettings(
            company_id=company.id,
            timezone=company_data.timezone,
            language=company_data.language,
            currency=company_data.currency,
            theme_color=company_data.theme_color,
            logo_url=company_data.logo_url,
            custom_domain=company_data.custom_domain,
            settings=company_data.settings,
        )
        await self.settings_repository.create(settings)

        return company
    
    async def get_company(self, company_id: UUID) -> Optional[Company]:
        """Get company by ID"""
        return await self.company_repository.get_by_id(company_id)
    
    async def get_company_by_slug(self, slug: str) -> Optional[Company]:
        """Get company by slug"""
        return await self.company_repository.get_by_slug(slug)
    
    async def get_all_companies(self, skip: int = 0, limit: int = 100) -> List[Company]:
        """Get all companies with pagination"""
        return await self.company_repository.get_all(skip, limit)
    
    async def update_company(self, company_id: UUID, company_data: CompanyUpdate) -> Optional[Company]:
        """Update company"""
        company = await self.company_repository.get_by_id(company_id)
        if not company:
            return None
        
        update_data = company_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(company, field, value)
        
        return await self.company_repository.update(company)
    
    async def delete_company(self, company_id: UUID) -> bool:
        """Delete company (soft delete)"""
        return await self.company_repository.delete(company_id)
    
    async def suspend_company(self, company_id: UUID) -> Optional[Company]:
        """Suspend company"""
        company = await self.company_repository.get_by_id(company_id)
        if not company:
            return None
        
        company.is_suspended = True
        return await self.company_repository.update(company)
    
    async def activate_company(self, company_id: UUID) -> Optional[Company]:
        """Activate company"""
        company = await self.company_repository.get_by_id(company_id)
        if not company:
            return None
        
        company.is_suspended = False
        company.is_active = True
        return await self.company_repository.update(company)
    
    async def create_company_settings(self, settings_data: CompanySettingsCreate) -> CompanySettings:
        """Create company settings"""
        settings = CompanySettings(
            company_id=settings_data.company_id,
            timezone=settings_data.timezone,
            language=settings_data.language,
            currency=settings_data.currency,
            theme_color=settings_data.theme_color,
            logo_url=settings_data.logo_url,
            custom_domain=settings_data.custom_domain,
            settings=settings_data.settings
        )
        return await self.settings_repository.create(settings)
    
    async def get_company_settings(self, company_id: UUID) -> Optional[CompanySettings]:
        """Get company settings"""
        return await self.settings_repository.get_by_company_id(company_id)
    
    async def update_company_settings(self, company_id: UUID, settings_data: CompanySettingsUpdate) -> Optional[CompanySettings]:
        """Update company settings"""
        settings = await self.settings_repository.get_by_company_id(company_id)
        if not settings:
            return None
        
        update_data = settings_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(settings, field, value)
        
        return await self.settings_repository.update(settings)
