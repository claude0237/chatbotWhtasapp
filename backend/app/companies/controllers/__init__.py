"""Company Controller"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.companies.services import CompanyService
from app.companies.schemas import (
    CompanyCreate, CompanyUpdate, CompanyResponse,
    CompanySettingsCreate, CompanySettingsUpdate, CompanySettingsResponse
)
from app.auth.dependencies import (
    get_current_active_user, get_current_company_id,
    require_company_admin, require_super_admin
)
from app.users.models import User


router = APIRouter(prefix="/companies", tags=["Companies"])


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Create a new company (super admin only)"""
    company_service = CompanyService(db)
    try:
        company = await company_service.create_company(company_data)
        return company
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    user_company_id: str = Depends(get_current_company_id)
):
    """Get company by ID"""
    company_service = CompanyService(db)
    company = await company_service.get_company(company_id)
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Multi-tenant check: user can only access their own company
    if str(company.id) != user_company_id and current_user.role.value != "SUPER_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return company


@router.get("", response_model=List[CompanyResponse])
@router.get("/", response_model=List[CompanyResponse])
async def get_companies(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Get all companies (super admin only)"""
    company_service = CompanyService(db)
    return await company_service.get_all_companies(skip, limit)


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    company_data: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
    user_company_id: str = Depends(get_current_company_id)
):
    """Update company"""
    company_service = CompanyService(db)
    
    # Multi-tenant check
    if company_id != user_company_id and current_user.role.value != "SUPER_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    company = await company_service.update_company(company_id, company_data)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Delete company (super admin only). System company cannot be deleted via API."""
    company_service = CompanyService(db)
    company = await company_service.get_company(company_id)
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    if company.slug == "system":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="L'entreprise System ne peut pas être supprimée. Suppression uniquement possible depuis la base de données."
        )
    
    success = await company_service.delete_company(company_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )


@router.post("/{company_id}/suspend", response_model=CompanyResponse)
async def suspend_company(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Suspend company (super admin only)"""
    company_service = CompanyService(db)
    company = await company_service.suspend_company(company_id)
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    return company


@router.post("/{company_id}/activate", response_model=CompanyResponse)
async def activate_company(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Activate company (super admin only)"""
    company_service = CompanyService(db)
    company = await company_service.activate_company(company_id)
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    return company


# Company Settings endpoints
@router.post("/{company_id}/settings", response_model=CompanySettingsResponse, status_code=status.HTTP_201_CREATED)
async def create_company_settings(
    company_id: str,
    settings_data: CompanySettingsCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
    user_company_id: str = Depends(get_current_company_id)
):
    """Create company settings"""
    company_service = CompanyService(db)
    
    # Multi-tenant check
    if company_id != user_company_id and current_user.role.value != "SUPER_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    settings_data.company_id = company_id
    settings = await company_service.create_company_settings(settings_data)
    return settings


@router.get("/{company_id}/settings", response_model=CompanySettingsResponse)
async def get_company_settings(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    user_company_id: str = Depends(get_current_company_id)
):
    """Get company settings"""
    company_service = CompanyService(db)
    
    # Multi-tenant check
    if company_id != user_company_id and current_user.role.value != "SUPER_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    settings = await company_service.get_company_settings(company_id)
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not found"
        )
    
    return settings


@router.put("/{company_id}/settings", response_model=CompanySettingsResponse)
async def update_company_settings(
    company_id: str,
    settings_data: CompanySettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
    user_company_id: str = Depends(get_current_company_id)
):
    """Update company settings"""
    company_service = CompanyService(db)
    
    # Multi-tenant check
    if company_id != user_company_id and current_user.role.value != "SUPER_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    settings = await company_service.update_company_settings(company_id, settings_data)
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not found"
        )
    
    return settings
