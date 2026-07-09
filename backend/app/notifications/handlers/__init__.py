"""Notification Event Handlers"""
from typing import Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.events import EventHandler, EventBus
from app.notifications.services import NotificationService
from app.notifications.models import NotificationType
from app.users.models import UserRoleEnum as UserRole


class NewConversationEventHandler(EventHandler):
    """Handler for new conversation events - notifies agents"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_service = NotificationService(db)
    
    async def handle(self, event_data: Dict[str, Any]):
        """Handle new conversation event"""
        company_id = event_data.get("company_id")
        conversation_id = event_data.get("conversation_id")
        customer_name = event_data.get("customer_name", "Unknown")
        
        if company_id:
            await self.notification_service.send_to_role(
                company_id=company_id,
                role=UserRole.AGENT,
                notification_type=NotificationType.NEW_CONVERSATION,
                title="Nouvelle conversation",
                message=f"Nouvelle conversation de {customer_name}",
                data={
                    "conversation_id": str(conversation_id) if conversation_id else None,
                    "customer_name": customer_name
                }
            )


class AgentMentionEventHandler(EventHandler):
    """Handler for agent mention events - notifies the mentioned agent"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_service = NotificationService(db)
    
    async def handle(self, event_data: Dict[str, Any]):
        """Handle agent mention event"""
        mentioned_agent_id = event_data.get("mentioned_agent_id")
        mentioning_user_id = event_data.get("mentioning_user_id")
        conversation_id = event_data.get("conversation_id")
        message = event_data.get("message")
        
        if mentioned_agent_id:
            await self.notification_service.send_to_user(
                user_id=mentioned_agent_id,
                notification_type=NotificationType.MENTION,
                title="Vous avez été mentionné",
                message=f"Quelqu'un vous a mentionné dans une conversation",
                data={
                    "conversation_id": str(conversation_id) if conversation_id else None,
                    "mentioning_user_id": str(mentioning_user_id) if mentioning_user_id else None,
                    "message": message
                }
            )


class ReservationCreatedEventHandler(EventHandler):
    """Handler for reservation created events - notifies admins"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_service = NotificationService(db)
    
    async def handle(self, event_data: Dict[str, Any]):
        """Handle reservation created event"""
        company_id = event_data.get("company_id")
        reservation_id = event_data.get("reservation_id")
        customer_name = event_data.get("customer_name", "Unknown")
        reservation_date = event_data.get("reservation_date")
        
        if company_id:
            await self.notification_service.send_to_role(
                company_id=company_id,
                role=UserRole.ADMIN,
                notification_type=NotificationType.RESERVATION,
                title="Nouvelle réservation",
                message=f"Nouvelle réservation de {customer_name} pour le {reservation_date}",
                data={
                    "reservation_id": str(reservation_id) if reservation_id else None,
                    "customer_name": customer_name,
                    "reservation_date": reservation_date
                }
            )


class PaymentReceivedEventHandler(EventHandler):
    """Handler for payment received events - notifies admins"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_service = NotificationService(db)
    
    async def handle(self, event_data: Dict[str, Any]):
        """Handle payment received event"""
        company_id = event_data.get("company_id")
        payment_id = event_data.get("payment_id")
        amount = event_data.get("amount")
        customer_name = event_data.get("customer_name", "Unknown")
        
        if company_id:
            await self.notification_service.send_to_role(
                company_id=company_id,
                role=UserRole.ADMIN,
                notification_type=NotificationType.PAYMENT,
                title="Paiement reçu",
                message=f"Paiement de {amount} reçu de {customer_name}",
                data={
                    "payment_id": str(payment_id) if payment_id else None,
                    "amount": amount,
                    "customer_name": customer_name
                }
            )


def register_notification_handlers(event_bus: EventBus, db: AsyncSession):
    """Register all notification event handlers"""
    event_bus.subscribe("conversation_created", NewConversationEventHandler(db))
    event_bus.subscribe("agent_mentioned", AgentMentionEventHandler(db))
    event_bus.subscribe("reservation_created", ReservationCreatedEventHandler(db))
    event_bus.subscribe("payment_received", PaymentReceivedEventHandler(db))
