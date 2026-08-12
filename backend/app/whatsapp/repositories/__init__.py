"""WhatsApp Repository"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.whatsapp.models import WhatsAppMessage, WhatsAppTemplate, WebhookEvent, MessageStatus


class WhatsAppMessageRepository:
    """Repository for WhatsAppMessage model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, message: WhatsAppMessage) -> WhatsAppMessage:
        """Create a new message"""
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message
    
    async def get_by_id(self, message_id: UUID) -> Optional[WhatsAppMessage]:
        """Get message by ID"""
        result = await self.db.execute(
            select(WhatsAppMessage).where(WhatsAppMessage.id == message_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_whatsapp_id(self, whatsapp_message_id: str) -> Optional[WhatsAppMessage]:
        """Get message by WhatsApp message ID"""
        result = await self.db.execute(
            select(WhatsAppMessage).where(WhatsAppMessage.message_id == whatsapp_message_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_company_id(self, company_id: UUID, skip: int = 0, limit: int = 100) -> List[WhatsAppMessage]:
        """Get messages by company ID with pagination"""
        result = await self.db.execute(
            select(WhatsAppMessage)
            .where(WhatsAppMessage.company_id == company_id)
            .order_by(WhatsAppMessage.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_phone_number(self, company_id: UUID, phone_number: str, skip: int = 0, limit: int = 100) -> List[WhatsAppMessage]:
        """Get messages by phone number for a company"""
        result = await self.db.execute(
            select(WhatsAppMessage)
            .where(
                and_(
                    WhatsAppMessage.company_id == company_id,
                    WhatsAppMessage.phone_number == phone_number
                )
            )
            .order_by(WhatsAppMessage.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_by_company_id(self, company_id: UUID) -> int:
        """Count total messages for a company"""
        result = await self.db.execute(
            select(func.count(WhatsAppMessage.id))
            .where(WhatsAppMessage.company_id == company_id)
        )
        return result.scalar() or 0

    async def count_by_phone_number(self, company_id: UUID, phone_number: str) -> int:
        """Count total messages for a phone number in a company"""
        result = await self.db.execute(
            select(func.count(WhatsAppMessage.id))
            .where(
                and_(
                    WhatsAppMessage.company_id == company_id,
                    WhatsAppMessage.phone_number == phone_number
                )
            )
        )
        return result.scalar() or 0
    
    async def update_status(self, message_id: UUID, status: MessageStatus) -> Optional[WhatsAppMessage]:
        """Update message status"""
        message = await self.get_by_id(message_id)
        if message:
            message.status = status
            if status == MessageStatus.DELIVERED:
                message.delivered_at = datetime.utcnow()
            elif status == MessageStatus.READ:
                message.read_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(message)
            return message
        return None
    
    async def update(self, message: WhatsAppMessage) -> WhatsAppMessage:
        """Update message"""
        await self.db.commit()
        await self.db.refresh(message)
        return message


class WhatsAppTemplateRepository:
    """Repository for WhatsAppTemplate model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, template: WhatsAppTemplate) -> WhatsAppTemplate:
        """Create a new template"""
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template
    
    async def get_by_id(self, template_id: UUID) -> Optional[WhatsAppTemplate]:
        """Get template by ID"""
        result = await self.db.execute(
            select(WhatsAppTemplate).where(WhatsAppTemplate.id == template_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, company_id: UUID, name: str) -> Optional[WhatsAppTemplate]:
        """Get template by name for a company"""
        result = await self.db.execute(
            select(WhatsAppTemplate).where(
                and_(
                    WhatsAppTemplate.company_id == company_id,
                    WhatsAppTemplate.name == name
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_company_id(self, company_id: UUID, skip: int = 0, limit: int = 100) -> List[WhatsAppTemplate]:
        """Get templates by company ID with pagination"""
        result = await self.db.execute(
            select(WhatsAppTemplate)
            .where(WhatsAppTemplate.company_id == company_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_active_templates(self, company_id: UUID) -> List[WhatsAppTemplate]:
        """Get all active templates for a company"""
        result = await self.db.execute(
            select(WhatsAppTemplate).where(
                and_(
                    WhatsAppTemplate.company_id == company_id,
                    WhatsAppTemplate.is_active == True
                )
            )
        )
        return result.scalars().all()
    
    async def update(self, template: WhatsAppTemplate) -> WhatsAppTemplate:
        """Update template"""
        await self.db.commit()
        await self.db.refresh(template)
        return template
    
    async def delete(self, template_id: UUID) -> bool:
        """Delete template by ID"""
        template = await self.get_by_id(template_id)
        if template:
            await self.db.delete(template)
            await self.db.commit()
            return True
        return False


class WebhookEventRepository:
    """Repository for WebhookEvent model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, event: WebhookEvent) -> WebhookEvent:
        """Create a new webhook event"""
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event
    
    async def get_by_id(self, event_id: UUID) -> Optional[WebhookEvent]:
        """Get event by ID"""
        result = await self.db.execute(
            select(WebhookEvent).where(WebhookEvent.id == event_id)
        )
        return result.scalar_one_or_none()
    
    async def get_unprocessed_events(self, company_id: UUID, limit: int = 100) -> List[WebhookEvent]:
        """Get unprocessed events for a company"""
        result = await self.db.execute(
            select(WebhookEvent)
            .where(
                and_(
                    WebhookEvent.company_id == company_id,
                    WebhookEvent.processed == False
                )
            )
            .order_by(WebhookEvent.received_at.asc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def mark_as_processed(self, event_id: UUID) -> Optional[WebhookEvent]:
        """Mark event as processed"""
        event = await self.get_by_id(event_id)
        if event:
            event.processed = True
            event.processed_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(event)
            return event
        return None
    
    async def mark_as_failed(self, event_id: UUID, error_message: str) -> Optional[WebhookEvent]:
        """Mark event as failed"""
        event = await self.get_by_id(event_id)
        if event:
            event.processed = True
            event.error_message = error_message
            event.processed_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(event)
            return event
        return None
    
    async def get_by_event_type(self, company_id: UUID, event_type: str, skip: int = 0, limit: int = 100) -> List[WebhookEvent]:
        """Get events by event type for a company"""
        result = await self.db.execute(
            select(WebhookEvent)
            .where(
                and_(
                    WebhookEvent.company_id == company_id,
                    WebhookEvent.event_type == event_type
                )
            )
            .order_by(WebhookEvent.received_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
