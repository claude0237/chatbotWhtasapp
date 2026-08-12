"""Conversation Repository"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.conversations.models import Conversation, Message, ConversationNote, ConversationStatus, ConversationMessageStatus
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
    
    async def update_profile(self, customer_id: UUID, name: Optional[str] = None, profile_picture_url: Optional[str] = None, extra_data: Optional[dict] = None) -> Optional[Customer]:
        """Update customer profile"""
        customer = await self.get_by_id(customer_id)
        if customer:
            if name is not None:
                customer.name = name
            if profile_picture_url is not None:
                customer.profile_picture_url = profile_picture_url
            if extra_data is not None:
                customer.extra_data = extra_data
            await self.db.commit()
            await self.db.refresh(customer)
            return customer
        return None
    
    async def update(self, customer: Customer) -> Customer:
        """Update customer"""
        await self.db.commit()
        await self.db.refresh(customer)
        return customer


class ConversationRepository:
    """Repository for Conversation model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, conversation: Conversation) -> Conversation:
        """Create a new conversation"""
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation
    
    async def get_by_id(self, conversation_id: UUID) -> Optional[Conversation]:
        """Get conversation by ID"""
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_customer_id(self, customer_id: UUID, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Get conversations by customer ID with pagination"""
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.customer_id == customer_id)
            .order_by(Conversation.last_activity_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_active_by_customer(self, company_id: UUID, customer_id: UUID) -> Optional[Conversation]:
        """Get active conversation for a customer"""
        result = await self.db.execute(
            select(Conversation).where(
                and_(
                    Conversation.company_id == company_id,
                    Conversation.customer_id == customer_id,
                    Conversation.status == ConversationStatus.OPEN
                )
            ).order_by(Conversation.last_activity_at.desc())
        )
        return result.scalar_one_or_none()
    
    async def get_by_company_id(self, company_id: UUID, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Get conversations by company ID with pagination"""
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.company_id == company_id)
            .order_by(Conversation.last_activity_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_by_company_id(self, company_id: UUID) -> int:
        """Count total conversations for a company"""
        result = await self.db.execute(
            select(func.count(Conversation.id))
            .where(Conversation.company_id == company_id)
        )
        return result.scalar() or 0
    
    async def get_by_status(self, company_id: UUID, status: ConversationStatus, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Get conversations by status for a company"""
        result = await self.db.execute(
            select(Conversation)
            .where(
                and_(
                    Conversation.company_id == company_id,
                    Conversation.status == status
                )
            )
            .order_by(Conversation.last_activity_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_agent_id(self, agent_id: UUID, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Get conversations assigned to an agent"""
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.assigned_agent_id == agent_id)
            .order_by(Conversation.last_activity_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def assign_to_agent(self, conversation_id: UUID, agent_id: UUID) -> Optional[Conversation]:
        """Assign conversation to an agent — status becomes WAITING until the agent writes"""
        conversation = await self.get_by_id(conversation_id)
        if conversation:
            conversation.assigned_agent_id = agent_id
            conversation.status = ConversationStatus.WAITING
            conversation.last_activity_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(conversation)
            return conversation
        return None
    
    async def change_status(self, conversation_id: UUID, status: ConversationStatus) -> Optional[Conversation]:
        """Change conversation status"""
        conversation = await self.get_by_id(conversation_id)
        if conversation:
            conversation.status = status
            conversation.last_activity_at = datetime.utcnow()
            if status == ConversationStatus.CLOSED:
                conversation.closed_at = datetime.utcnow()
            elif status == ConversationStatus.ARCHIVED:
                conversation.archived_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(conversation)
            return conversation
        return None
    
    async def add_tag(self, conversation_id: UUID, tag: str) -> Optional[Conversation]:
        """Add a tag to conversation"""
        conversation = await self.get_by_id(conversation_id)
        if conversation:
            if conversation.tags is None:
                conversation.tags = []
            if tag not in conversation.tags:
                conversation.tags.append(tag)
            await self.db.commit()
            await self.db.refresh(conversation)
            return conversation
        return None
    
    async def archive(self, conversation_id: UUID) -> Optional[Conversation]:
        """Archive conversation"""
        return await self.change_status(conversation_id, ConversationStatus.ARCHIVED)
    
    async def update(self, conversation: Conversation) -> Conversation:
        """Update conversation"""
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation

    async def delete(self, conversation_id: UUID) -> bool:
        """Delete conversation and all related data (cascade)"""
        conversation = await self.get_by_id(conversation_id)
        if conversation:
            await self.db.delete(conversation)
            await self.db.commit()
            return True
        return False

    async def get_unassigned_open(self, company_id: UUID) -> List[Conversation]:
        """Get open/waiting conversations with no assigned agent, ordered oldest first"""
        result = await self.db.execute(
            select(Conversation)
            .where(
                and_(
                    Conversation.company_id == company_id,
                    Conversation.assigned_agent_id == None,
                    or_(
                        Conversation.status == ConversationStatus.OPEN,
                        Conversation.status == ConversationStatus.WAITING,
                    )
                )
            )
            .order_by(Conversation.created_at.asc())
        )
        return result.scalars().all()

    async def get_agent_load(self, company_id: UUID, agent_ids: List[UUID]) -> dict:
        """Return {agent_id: count_of_open_assigned_conversations} for given agents"""
        if not agent_ids:
            return {}
        result = await self.db.execute(
            select(Conversation)
            .where(
                and_(
                    Conversation.company_id == company_id,
                    Conversation.assigned_agent_id.in_(agent_ids),
                    Conversation.status.in_([
                        ConversationStatus.OPEN,
                        ConversationStatus.WAITING,
                        ConversationStatus.AGENT,
                    ])
                )
            )
        )
        convs = result.scalars().all()
        load: dict = {str(aid): 0 for aid in agent_ids}
        for c in convs:
            key = str(c.assigned_agent_id)
            load[key] = load.get(key, 0) + 1
        return load


class MessageRepository:
    """Repository for Message model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, message: Message) -> Message:
        """Create a new message"""
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message
    
    async def get_by_id(self, message_id: UUID) -> Optional[Message]:
        """Get message by ID"""
        result = await self.db.execute(
            select(Message).where(Message.id == message_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_conversation_id(self, conversation_id: UUID, skip: int = 0, limit: int = 100) -> List[Message]:
        """Get messages by conversation ID with pagination"""
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sent_at.asc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_external_id(self, external_message_id: str) -> Optional[Message]:
        """Get message by external message ID (e.g., WhatsApp message ID)"""
        result = await self.db.execute(
            select(Message).where(Message.external_message_id == external_message_id)
        )
        return result.scalar_one_or_none()
    
    async def update_status(self, message_id: UUID, status: ConversationMessageStatus) -> Optional[Message]:
        """Update message status"""
        message = await self.get_by_id(message_id)
        if message:
            message.status = status
            if status == ConversationMessageStatus.DELIVERED:
                message.delivered_at = datetime.utcnow()
            elif status == ConversationMessageStatus.READ:
                message.read_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(message)
            return message
        return None
    
    async def get_history(self, conversation_id: UUID, limit: int = 100) -> List[Message]:
        """Get message history for a conversation"""
        return await self.get_by_conversation_id(conversation_id, 0, limit)
    
    async def update(self, message: Message) -> Message:
        """Update message"""
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def delete(self, message_id: UUID) -> bool:
        """Delete a single message"""
        message = await self.get_by_id(message_id)
        if message:
            await self.db.delete(message)
            await self.db.commit()
            return True
        return False


class ConversationNoteRepository:
    """Repository for ConversationNote model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, note: ConversationNote) -> ConversationNote:
        """Create a new conversation note"""
        self.db.add(note)
        await self.db.commit()
        await self.db.refresh(note)
        return note
    
    async def get_by_id(self, note_id: UUID) -> Optional[ConversationNote]:
        """Get note by ID"""
        result = await self.db.execute(
            select(ConversationNote).where(ConversationNote.id == note_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_conversation_id(self, conversation_id: UUID) -> List[ConversationNote]:
        """Get notes by conversation ID"""
        result = await self.db.execute(
            select(ConversationNote)
            .where(ConversationNote.conversation_id == conversation_id)
            .order_by(ConversationNote.created_at.desc())
        )
        return result.scalars().all()
    
    async def update(self, note: ConversationNote) -> ConversationNote:
        """Update note"""
        await self.db.commit()
        await self.db.refresh(note)
        return note
    
    async def delete(self, note_id: UUID) -> bool:
        """Delete note by ID"""
        note = await self.get_by_id(note_id)
        if note:
            await self.db.delete(note)
            await self.db.commit()
            return True
        return False
