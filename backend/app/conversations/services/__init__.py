"""Conversation Service"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.conversations.models import Conversation, Message, ConversationStatus, ConversationPriority, SenderType, ConversationMessageType, ConversationMessageStatus
from app.customers.models import Customer
from app.conversations.repositories import CustomerRepository, ConversationRepository, MessageRepository, ConversationNoteRepository
from app.bot.services import NativeBotEngine


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
        extra_data: Optional[dict] = None
    ) -> Optional[Customer]:
        """Update customer profile"""
        return await self.repository.update_profile(customer_id, name, profile_picture_url, extra_data)
    
    async def get_by_id(self, customer_id: UUID) -> Optional[Customer]:
        """Get customer by ID"""
        return await self.repository.get_by_id(customer_id)
    
    async def get_by_company_id(self, company_id: UUID, skip: int = 0, limit: int = 100) -> List[Customer]:
        """Get customers by company ID"""
        return await self.repository.get_by_company_id(company_id, skip, limit)


class ConversationService:
    """Service for Conversation operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = ConversationRepository(db)
    
    async def create_conversation(
        self,
        company_id: UUID,
        customer_id: UUID,
        channel_id: Optional[UUID] = None,
        status: ConversationStatus = ConversationStatus.OPEN,
        priority: ConversationPriority = ConversationPriority.MEDIUM
    ) -> Conversation:
        """Create a new conversation"""
        conversation = Conversation(
            company_id=company_id,
            customer_id=customer_id,
            channel_id=channel_id,
            status=status,
            priority=priority
        )
        return await self.repository.create(conversation)
    
    async def assign_to_agent(self, conversation_id: UUID, agent_id: UUID) -> Optional[Conversation]:
        """Assign conversation to an agent"""
        return await self.repository.assign_to_agent(conversation_id, agent_id)
    
    async def change_status(self, conversation_id: UUID, status: ConversationStatus) -> Optional[Conversation]:
        """Change conversation status"""
        return await self.repository.change_status(conversation_id, status)
    
    async def add_tag(self, conversation_id: UUID, tag: str) -> Optional[Conversation]:
        """Add a tag to conversation"""
        return await self.repository.add_tag(conversation_id, tag)
    
    async def archive(self, conversation_id: UUID) -> Optional[Conversation]:
        """Archive conversation"""
        return await self.repository.archive(conversation_id)
    
    async def get_by_id(self, conversation_id: UUID) -> Optional[Conversation]:
        """Get conversation by ID"""
        return await self.repository.get_by_id(conversation_id)
    
    async def get_by_customer_id(self, customer_id: UUID, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Get conversations by customer ID"""
        return await self.repository.get_by_customer_id(customer_id, skip, limit)
    
    async def get_by_company_id(self, company_id: UUID, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Get conversations by company ID"""
        return await self.repository.get_by_company_id(company_id, skip, limit)
    
    async def get_by_status(self, company_id: UUID, status: ConversationStatus, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Get conversations by status for a company"""
        return await self.repository.get_by_status(company_id, status, skip, limit)
    
    async def get_by_agent_id(self, agent_id: UUID, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Get conversations assigned to an agent"""
        return await self.repository.get_by_agent_id(agent_id, skip, limit)

    async def auto_assign_round_robin(self, company_id: UUID, agent_ids: List[UUID]) -> dict:
        """
        Round-robin auto-assign: distribute unassigned OPEN/WAITING conversations
        evenly across agents, always picking the one with fewest active conversations.
        Returns {'assigned': int, 'skipped': int, 'assignments': [{conv_id, agent_id}]}
        """
        if not agent_ids:
            return {"assigned": 0, "skipped": 0, "assignments": []}

        unassigned = await self.repository.get_unassigned_open(company_id)
        if not unassigned:
            return {"assigned": 0, "skipped": 0, "assignments": []}

        load = await self.repository.get_agent_load(company_id, agent_ids)

        assignments = []
        for conv in unassigned:
            agent_id = min(agent_ids, key=lambda a: load.get(str(a), 0))
            updated = await self.repository.assign_to_agent(conv.id, agent_id)
            if updated:
                load[str(agent_id)] = load.get(str(agent_id), 0) + 1
                assignments.append({"conversation_id": str(conv.id), "agent_id": str(agent_id)})

        return {
            "assigned": len(assignments),
            "skipped": len(unassigned) - len(assignments),
            "assignments": assignments,
        }


    async def delete_conversation(self, conversation_id: UUID) -> bool:
        """Delete a conversation and clean up related WhatsApp messages and bot state"""
        conversation = await self.repository.get_by_id(conversation_id)
        if not conversation:
            return False
        # Clean up bot conversation state for this contact
        from app.bot.repositories import BotConversationStateRepository
        state_repo = BotConversationStateRepository(self.db)
        # Fetch customer phone to clear bot state
        customer_repo = CustomerRepository(self.db)
        customer = await customer_repo.get_by_id(conversation.customer_id)
        if customer:
            orphan = await state_repo.get_active(conversation.company_id, customer.phone_number)
            if orphan:
                await state_repo.delete(orphan)
            # Delete WhatsApp raw messages for this phone + company
            from app.whatsapp.repositories import WhatsAppMessageRepository
            wa_repo = WhatsAppMessageRepository(self.db)
            wa_messages = await wa_repo.get_by_phone_number(
                conversation.company_id, customer.phone_number, skip=0, limit=10000
            )
            for wm in wa_messages:
                await self.db.delete(wm)
        # Delete conversation (cascades to messages + notes)
        return await self.repository.delete(conversation_id)


class MessageService:
    """Service for Message operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = MessageRepository(db)
    
    async def send_message(
        self,
        conversation_id: UUID,
        sender_type: SenderType,
        sender_id: Optional[UUID],
        content: str,
        message_type: ConversationMessageType = ConversationMessageType.TEXT,
        media_url: Optional[str] = None,
        external_message_id: Optional[str] = None
    ) -> Message:
        """Send a message"""
        message = Message(
            conversation_id=conversation_id,
            sender_type=sender_type,
            sender_id=sender_id,
            content=content,
            message_type=message_type,
            media_url=media_url,
            external_message_id=external_message_id,
            status=ConversationMessageStatus.SENT
        )
        return await self.repository.create(message)
    
    async def receive_message(
        self,
        conversation_id: UUID,
        sender_type: SenderType,
        sender_id: Optional[UUID],
        content: str,
        message_type: ConversationMessageType = ConversationMessageType.TEXT,
        media_url: Optional[str] = None,
        external_message_id: Optional[str] = None
    ) -> Message:
        """Receive a message from external source (e.g., WhatsApp)"""
        message = Message(
            conversation_id=conversation_id,
            sender_type=sender_type,
            sender_id=sender_id,
            content=content,
            message_type=message_type,
            media_url=media_url,
            external_message_id=external_message_id,
            status=ConversationMessageStatus.DELIVERED
        )
        created_message = await self.repository.create(message)
        
        # If message is from customer, trigger bot response
        if sender_type == SenderType.CUSTOMER and content:
            await self._trigger_bot_response(conversation_id, content)
        
        return created_message
    
    async def _trigger_bot_response(self, conversation_id: UUID, customer_message: str):
        """Trigger bot response for customer message"""
        # Get conversation to get company_id
        conversation = await ConversationRepository(self.db).get_by_id(conversation_id)
        if not conversation:
            return
        
        # Only trigger bot if conversation is in AI or OPEN status (automatic routing)
        if conversation.status not in [ConversationStatus.AI, ConversationStatus.OPEN]:
            return
        
        # Get bot configuration to determine routing
        from app.bot.repositories import BotConfigurationRepository
        from app.bot.models import BotType
        config_repo = BotConfigurationRepository(self.db)
        config = await config_repo.get_active_configuration(conversation.company_id)
        
        if not config:
            return
        
        bot_response = None
        
        # Route based on bot type
        if config.bot_type in [BotType.ML, BotType.HYBRID] and config.ml_enabled:
            # Use ML Engine with fallback
            from app.ml.engine import MLEngine
            from app.bot.services import NativeBotEngine
            
            ml_engine = MLEngine(self.db)
            native_engine = NativeBotEngine(self.db)
            
            # Get native response for fallback
            native_response = await native_engine.process_message(conversation.company_id, customer_message)
            
            # Process with ML and fallback
            ml_result = await ml_engine.process_with_fallback(
                company_id=conversation.company_id,
                message=customer_message,
                native_response=native_response
            )
            
            bot_response = ml_result["response"]
        else:
            # Use Native Bot Engine
            bot_engine = NativeBotEngine(self.db)
            bot_response = await bot_engine.process_message(conversation.company_id, customer_message)
        
        # Send bot response
        if bot_response:
            await self.send_message(
                conversation_id=conversation_id,
                sender_type=SenderType.BOT,
                sender_id=None,
                content=bot_response,
                message_type=ConversationMessageType.TEXT
            )
            
            # Update conversation status to AI if it was OPEN
            if conversation.status == ConversationStatus.OPEN:
                await ConversationRepository(self.db).change_status(conversation_id, ConversationStatus.AI)
    
    async def transfer_to_agent(self, conversation_id: UUID, agent_id: UUID) -> Optional[Conversation]:
        """Transfer conversation from bot to agent"""
        conversation_repo = ConversationRepository(self.db)
        return await conversation_repo.assign_to_agent(conversation_id, agent_id)
    
    async def transfer_to_bot(self, conversation_id: UUID) -> Optional[Conversation]:
        """Transfer conversation from agent to bot"""
        conversation_repo = ConversationRepository(self.db)
        return await conversation_repo.change_status(conversation_id, ConversationStatus.AI)
    
    async def update_status(self, message_id: UUID, status: ConversationMessageStatus) -> Optional[Message]:
        """Update message status"""
        return await self.repository.update_status(message_id, status)
    
    async def get_history(self, conversation_id: UUID, limit: int = 100) -> List[Message]:
        """Get message history for a conversation"""
        return await self.repository.get_history(conversation_id, limit)
    
    async def get_by_id(self, message_id: UUID) -> Optional[Message]:
        """Get message by ID"""
        return await self.repository.get_by_id(message_id)
    
    async def get_by_conversation_id(self, conversation_id: UUID, skip: int = 0, limit: int = 100) -> List[Message]:
        """Get messages by conversation ID"""
        return await self.repository.get_by_conversation_id(conversation_id, skip, limit)
    
    async def get_by_external_id(self, external_message_id: str) -> Optional[Message]:
        """Get message by external message ID"""
        return await self.repository.get_by_external_id(external_message_id)

    async def delete_message(self, message_id: UUID) -> bool:
        """Delete a single message"""
        return await self.repository.delete(message_id)
