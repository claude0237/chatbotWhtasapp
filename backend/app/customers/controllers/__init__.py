"""Customer Controller"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel
from uuid import UUID

from app.database import get_db
from app.customers.services import CustomerService
from app.auth.dependencies import get_current_active_user, get_current_company_id
from app.users.models import User
from app.conversations.models import Conversation


router = APIRouter(prefix="/customers", tags=["Customers"])


class CustomerResponse(BaseModel):
    """Customer response schema"""
    id: str
    company_id: str
    phone_number: str
    name: Optional[str]
    profile_picture_url: Optional[str]
    extra_data: Optional[dict]
    first_seen_at: str
    last_seen_at: str
    created_at: str
    updated_at: str


class CustomerUpdateRequest(BaseModel):
    """Customer update request schema — all fields stored in extra_data except name/photo"""
    name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    email: Optional[str] = None
    company_name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    notes: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[dict] = None


@router.get("")
@router.get("/")
async def get_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get customers for the current user's company"""
    customer_service = CustomerService(db)
    from app.customers.repositories import CustomerRepository
    cust_repo = CustomerRepository(db)
    
    customers = await customer_service.get_by_company_id(
        company_id=UUID(company_id),
        skip=skip,
        limit=limit
    )

    total = await cust_repo.count_by_company_id(UUID(company_id))
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "customers": [
            {
                "id": str(customer.id),
                "company_id": str(customer.company_id),
                "phone_number": customer.phone_number,
                "name": customer.name,
                "profile_picture_url": customer.profile_picture_url,
                "extra_data": customer.extra_data,
                "first_seen_at": customer.first_seen_at.isoformat(),
                "last_seen_at": customer.last_seen_at.isoformat(),
                "created_at": customer.created_at.isoformat(),
                "updated_at": customer.updated_at.isoformat()
            }
            for customer in customers
        ]
    }


@router.get("/{customer_id}")
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get a specific customer"""
    customer_service = CustomerService(db)
    
    customer = await customer_service.get_by_id(UUID(customer_id))
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Verify customer belongs to user's company
    if str(customer.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return {
        "id": str(customer.id),
        "company_id": str(customer.company_id),
        "phone_number": customer.phone_number,
        "name": customer.name,
        "profile_picture_url": customer.profile_picture_url,
        "extra_data": customer.extra_data,
        "first_seen_at": customer.first_seen_at.isoformat(),
        "last_seen_at": customer.last_seen_at.isoformat(),
        "created_at": customer.created_at.isoformat(),
        "updated_at": customer.updated_at.isoformat()
    }


@router.put("/{customer_id}")
async def update_customer(
    customer_id: str,
    request: CustomerUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Update a customer"""
    customer_service = CustomerService(db)
    
    customer = await customer_service.get_by_id(UUID(customer_id))
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Verify customer belongs to user's company
    if str(customer.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    extra_data: dict = request.custom_fields or {}
    for field in ("email", "company_name", "city", "country", "language", "notes", "source", "tags"):
        value = getattr(request, field, None)
        if value is not None:
            extra_data[field] = value

    updated_customer = await customer_service.update_profile(
        UUID(customer_id),
        name=request.name,
        profile_picture_url=request.profile_picture_url,
        metadata=extra_data if extra_data else None
    )

    return {
        "id": str(updated_customer.id),
        "company_id": str(updated_customer.company_id),
        "phone_number": updated_customer.phone_number,
        "name": updated_customer.name,
        "profile_picture_url": updated_customer.profile_picture_url,
        "extra_data": updated_customer.extra_data,
        "first_seen_at": updated_customer.first_seen_at.isoformat(),
        "last_seen_at": updated_customer.last_seen_at.isoformat(),
        "created_at": updated_customer.created_at.isoformat(),
        "updated_at": updated_customer.updated_at.isoformat()
    }


@router.delete("/{customer_id}", status_code=status.HTTP_200_OK)
async def delete_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Delete a customer and all related data (conversations, messages, WhatsApp messages, bot state)"""
    customer_service = CustomerService(db)
    customer = await customer_service.get_by_id(UUID(customer_id))
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    if str(customer.company_id) != company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    deleted = await customer_service.delete_customer(UUID(customer_id))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete customer")
    return {"status": "deleted", "id": customer_id}


@router.get("/{customer_id}/conversations")
async def get_customer_conversations(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get conversation history for a specific customer"""
    customer_service = CustomerService(db)
    customer = await customer_service.get_by_id(UUID(customer_id))
    if not customer or str(customer.company_id) != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    result = await db.execute(
        select(Conversation)
        .where(and_(Conversation.customer_id == UUID(customer_id), Conversation.company_id == UUID(company_id)))
        .order_by(Conversation.last_activity_at.desc())
        .limit(20)
    )
    convs = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "status": c.status.value,
            "priority": c.priority.value,
            "assigned_agent_id": str(c.assigned_agent_id) if c.assigned_agent_id else None,
            "last_activity_at": c.last_activity_at.isoformat(),
            "created_at": c.created_at.isoformat(),
        }
        for c in convs
    ]
