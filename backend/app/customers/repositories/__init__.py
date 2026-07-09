"""Customer Repository"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.customers.models import Customer


class CustomerRepository:
    """Repository for Customer model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, customer: Customer) -> Customer:
        """Create a new customer"""
        self.db.add(customer)
        await self.db.commit()
        await self.db.refresh(customer)
        return customer
    
    async def get_by_id(self, customer_id: UUID) -> Optional[Customer]:
        """Get customer by ID"""
        result = await self.db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_phone_number(self, company_id: UUID, phone_number: str) -> Optional[Customer]:
        """Get customer by phone number for a company"""
        result = await self.db.execute(
            select(Customer).where(
                and_(
                    Customer.company_id == company_id,
                    Customer.phone_number == phone_number
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_or_create(self, company_id: UUID, phone_number: str, name: Optional[str] = None) -> Customer:
        """Get existing customer or create new one"""
        customer = await self.get_by_phone_number(company_id, phone_number)
        if customer:
            # Update last seen
            customer.last_seen_at = datetime.utcnow()
            if name and not customer.name:
                customer.name = name
            await self.db.commit()
            await self.db.refresh(customer)
            return customer
        
        # Create new customer
        customer = Customer(
            company_id=company_id,
            phone_number=phone_number,
            name=name
        )
        return await self.create(customer)
    
    async def get_by_company_id(self, company_id: UUID, skip: int = 0, limit: int = 100) -> List[Customer]:
        """Get customers by company ID with pagination"""
        result = await self.db.execute(
            select(Customer)
            .where(Customer.company_id == company_id)
            .order_by(Customer.last_seen_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_by_company_id(self, company_id: UUID) -> int:
        """Count total customers for a company"""
        result = await self.db.execute(
            select(func.count(Customer.id))
            .where(Customer.company_id == company_id)
        )
        return result.scalar() or 0
    
    async def update_profile(self, customer_id: UUID, name: Optional[str] = None, profile_picture_url: Optional[str] = None, metadata: Optional[dict] = None) -> Optional[Customer]:
        """Update customer profile"""
        customer = await self.get_by_id(customer_id)
        if customer:
            if name is not None:
                customer.name = name
            if profile_picture_url is not None:
                customer.profile_picture_url = profile_picture_url
            if metadata is not None:
                customer.extra_data = metadata
            await self.db.commit()
            await self.db.refresh(customer)
            return customer
        return None
    
    async def update(self, customer: Customer) -> Customer:
        """Update customer"""
        await self.db.commit()
        await self.db.refresh(customer)
        return customer

    async def delete(self, customer_id: UUID) -> bool:
        """Delete customer (cascades to conversations, messages, notes)"""
        customer = await self.get_by_id(customer_id)
        if customer:
            await self.db.delete(customer)
            await self.db.commit()
            return True
        return False
