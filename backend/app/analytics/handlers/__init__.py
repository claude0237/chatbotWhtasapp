"""Analytics Event Handlers"""
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.events import EventHandler, EventBus
from app.analytics.services import AnalyticsService


class MessageSentEventHandler(EventHandler):
    """Handler for tracking message sent events"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.analytics_service = AnalyticsService(db)
    
    async def handle(self, event_data: Dict[str, Any]):
        """Handle message sent event"""
        company_id = event_data.get("company_id")
        sender_type = event_data.get("sender_type")
        
        if company_id:
            await self.analytics_service.track_metric(
                company_id=company_id,
                metric_name="message_sent",
                metric_value=1.0,
                dimensions={
                    "sender_type": sender_type,
                    "message_type": event_data.get("message_type")
                }
            )


class MessageReceivedEventHandler(EventHandler):
    """Handler for tracking message received events"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.analytics_service = AnalyticsService(db)
    
    async def handle(self, event_data: Dict[str, Any]):
        """Handle message received event"""
        company_id = event_data.get("company_id")
        
        if company_id:
            await self.analytics_service.track_metric(
                company_id=company_id,
                metric_name="message_received",
                metric_value=1.0,
                dimensions={
                    "sender_type": event_data.get("sender_type")
                }
            )


class ConversationCreatedEventHandler(EventHandler):
    """Handler for tracking conversation created events"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.analytics_service = AnalyticsService(db)
    
    async def handle(self, event_data: Dict[str, Any]):
        """Handle conversation created event"""
        company_id = event_data.get("company_id")
        
        if company_id:
            await self.analytics_service.track_metric(
                company_id=company_id,
                metric_name="conversation_created",
                metric_value=1.0,
                dimensions={
                    "status": event_data.get("status"),
                    "source": event_data.get("source")
                }
            )


class ConversationAssignedEventHandler(EventHandler):
    """Handler for tracking conversation assigned events"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.analytics_service = AnalyticsService(db)
    
    async def handle(self, event_data: Dict[str, Any]):
        """Handle conversation assigned event"""
        company_id = event_data.get("company_id")
        agent_id = event_data.get("agent_id")
        
        if company_id:
            await self.analytics_service.track_metric(
                company_id=company_id,
                metric_name="conversation_assigned",
                metric_value=1.0,
                dimensions={
                    "agent_id": str(agent_id) if agent_id else None
                }
            )


class BotResponseEventHandler(EventHandler):
    """Handler for tracking bot response events"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.analytics_service = AnalyticsService(db)
    
    async def handle(self, event_data: Dict[str, Any]):
        """Handle bot response event"""
        company_id = event_data.get("company_id")
        source = event_data.get("source", "native")
        confidence = event_data.get("confidence", 0.0)
        
        if company_id:
            await self.analytics_service.track_metric(
                company_id=company_id,
                metric_name="ml_response",
                metric_value=confidence,
                dimensions={
                    "source": source,
                    "bot_type": event_data.get("bot_type")
                }
            )


class AgentResponseEventHandler(EventHandler):
    """Handler for tracking agent response events"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.analytics_service = AnalyticsService(db)
    
    async def handle(self, event_data: Dict[str, Any]):
        """Handle agent response event"""
        company_id = event_data.get("company_id")
        agent_id = event_data.get("agent_id")
        response_time = event_data.get("response_time", 0.0)
        
        if company_id:
            await self.analytics_service.track_metric(
                company_id=company_id,
                metric_name="agent_response",
                metric_value=1.0,
                dimensions={
                    "agent_id": str(agent_id) if agent_id else None
                }
            )
            
            # Track response time separately
            if response_time > 0:
                await self.analytics_service.track_metric(
                    company_id=company_id,
                    metric_name="response_time",
                    metric_value=response_time,
                    dimensions={
                        "agent_id": str(agent_id) if agent_id else None
                    }
                )


def register_analytics_handlers(event_bus: EventBus, db: AsyncSession):
    """Register all analytics event handlers"""
    event_bus.subscribe("message_sent", MessageSentEventHandler(db))
    event_bus.subscribe("message_received", MessageReceivedEventHandler(db))
    event_bus.subscribe("conversation_created", ConversationCreatedEventHandler(db))
    event_bus.subscribe("conversation_assigned", ConversationAssignedEventHandler(db))
    event_bus.subscribe("bot_response", BotResponseEventHandler(db))
    event_bus.subscribe("agent_response", AgentResponseEventHandler(db))
