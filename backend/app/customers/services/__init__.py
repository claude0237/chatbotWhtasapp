"""Customer Service"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.customers.models import Customer
from app.customers.repositories import CustomerRepository


class CustomerService:
    """Service for Customer operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = CustomerRepository(db)
    
    async def get_or_create(self, company_id: UUID, phone_number: str, name: Optional[str] = None) -> Customer:
        """Get existing customer or create new one"""
        return await self.repository.get_or_create(company_id, phone_number, name)
    
    async def update_profile(
        self,
        customer_id: UUID,
        name: Optional[str] = None,
        profile_picture_url: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Optional[Customer]:
        """Update customer profile"""
        return await self.repository.update_profile(customer_id, name, profile_picture_url, metadata)
    
    async def get_by_id(self, customer_id: UUID) -> Optional[Customer]:
        """Get customer by ID"""
        return await self.repository.get_by_id(customer_id)
    
    async def get_by_company_id(self, company_id: UUID, skip: int = 0, limit: int = 100) -> List[Customer]:
        """Get customers by company ID"""
        return await self.repository.get_by_company_id(company_id, skip, limit)

    async def delete_customer(self, customer_id: UUID) -> bool:
        """Delete customer and clean up related WhatsApp messages and bot state"""
        customer = await self.repository.get_by_id(customer_id)
        if not customer:
            return False
        # Clean up bot conversation state
        from app.bot.repositories import BotConversationStateRepository
        state_repo = BotConversationStateRepository(self.db)
        orphan = await state_repo.get_active(customer.company_id, customer.phone_number)
        if orphan:
            await state_repo.delete(orphan)
        # Delete WhatsApp raw messages for this phone + company
        from app.whatsapp.repositories import WhatsAppMessageRepository
        wa_repo = WhatsAppMessageRepository(self.db)
        wa_messages = await wa_repo.get_by_phone_number(
            customer.company_id, customer.phone_number, skip=0, limit=10000
        )
        for wm in wa_messages:
            await self.db.delete(wm)
        # Delete customer (cascades to conversations → messages → notes)
        return await self.repository.delete(customer_id)
