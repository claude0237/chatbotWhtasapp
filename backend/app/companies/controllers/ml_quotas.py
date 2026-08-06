"""ML Quotas Controller - Super Admin only"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.auth.dependencies import get_current_user, require_super_admin
from app.companies.models import MLQuota, SubscriptionPlan
from pydantic import BaseModel


class MLQuotaBase(BaseModel):
    plan: str
    monthly_requests: int
    daily_requests: int | None = None
    max_tokens_per_request: int | None = None
    price_per_1000_requests: int | None = None


class MLQuotaCreate(MLQuotaBase):
    pass


class MLQuotaUpdate(BaseModel):
    monthly_requests: int | None = None
    daily_requests: int | None = None
    max_tokens_per_request: int | None = None
    price_per_1000_requests: int | None = None


class MLQuotaResponse(MLQuotaBase):
    id: UUID
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


router = APIRouter(prefix="/ml-quotas", tags=["ML Quotas"])


@router.get("", response_model=list[MLQuotaResponse])
async def get_all_ml_quotas(
    current_user = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all ML quotas (Super Admin only)"""
    result = await db.execute(select(MLQuota))
    quotas = result.scalars().all()
    return quotas


@router.get("/{plan}", response_model=MLQuotaResponse)
async def get_ml_quota_by_plan(
    plan: str,
    current_user = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get ML quota for a specific plan (Super Admin only)"""
    result = await db.execute(select(MLQuota).where(MLQuota.plan == plan))
    quota = result.scalar_one_or_none()
    if not quota:
        raise HTTPException(status_code=404, detail="Quota not found for this plan")
    return quota


@router.post("", response_model=MLQuotaResponse, status_code=status.HTTP_201_CREATED)
async def create_ml_quota(
    quota_data: MLQuotaCreate,
    current_user = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create ML quota for a plan (Super Admin only)"""
    # Validate plan value
    valid_plans = [p.value for p in SubscriptionPlan]
    if quota_data.plan not in valid_plans:
        raise HTTPException(status_code=400, detail=f"Invalid plan. Must be one of: {valid_plans}")
    
    # Check if quota already exists for this plan
    existing = await db.execute(select(MLQuota).where(MLQuota.plan == quota_data.plan))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Quota already exists for this plan")
    
    quota = MLQuota(**quota_data.model_dump())
    db.add(quota)
    await db.commit()
    await db.refresh(quota)
    return quota


@router.put("/{plan}", response_model=MLQuotaResponse)
async def update_ml_quota(
    plan: str,
    quota_data: MLQuotaUpdate,
    current_user = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update ML quota for a plan (Super Admin only)"""
    result = await db.execute(select(MLQuota).where(MLQuota.plan == plan))
    quota = result.scalar_one_or_none()
    if not quota:
        raise HTTPException(status_code=404, detail="Quota not found for this plan")
    
    # Update fields
    for field, value in quota_data.model_dump(exclude_unset=True).items():
        setattr(quota, field, value)
    
    await db.commit()
    await db.refresh(quota)
    return quota


@router.delete("/{plan}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ml_quota(
    plan: str,
    current_user = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete ML quota for a plan (Super Admin only)"""
    result = await db.execute(select(MLQuota).where(MLQuota.plan == plan))
    quota = result.scalar_one_or_none()
    if not quota:
        raise HTTPException(status_code=404, detail="Quota not found for this plan")
    
    await db.delete(quota)
    await db.commit()
