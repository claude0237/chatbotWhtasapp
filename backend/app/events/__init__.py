"""Event System"""
from typing import Callable, Any, Dict, List
from dataclasses import dataclass
from datetime import datetime
import json
import asyncio
from app.config import settings


@dataclass
class Event:
    """Base event class"""
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime
    company_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "event_type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "company_id": self.company_id
        }
    
    def to_json(self) -> str:
        """Convert event to JSON"""
        return json.dumps(self.to_dict())


# Event types
class EventTypes:
    """Event type constants"""
    MESSAGE_RECEIVED = "MessageReceived"
    MESSAGE_SENT = "MessageSent"
    CONVERSATION_CREATED = "ConversationCreated"
    CONVERSATION_ASSIGNED = "ConversationAssigned"
    CONVERSATION_STATUS_CHANGED = "ConversationStatusChanged"
    CUSTOMER_CREATED = "CustomerCreated"
    CUSTOMER_UPDATED = "CustomerUpdated"


class EventBus:
    """Simple in-memory event bus (can be extended to use Redis Streams)"""
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._redis_client = None
    
    async def initialize(self):
        """Initialize event bus with Redis if available"""
        try:
            import redis.asyncio as redis
            self._redis_client = await redis.from_url(settings.redis_url)
        except Exception:
            # Redis not available, use in-memory only
            pass
    
    async def publish(self, event: Event):
        """Publish an event to the bus"""
        # Call local handlers
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                print(f"Error in event handler: {e}")
        
        # Publish to Redis if available
        if self._redis_client:
            try:
                await self._redis_client.publish(
                    f"events:{event.company_id}",
                    event.to_json()
                )
            except Exception as e:
                print(f"Error publishing to Redis: {e}")
    
    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to an event type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def unsubscribe(self, event_type: str, handler: Callable):
        """Unsubscribe from an event type"""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)
    
    async def close(self):
        """Close event bus connections"""
        if self._redis_client:
            await self._redis_client.close()


# Global event bus instance
event_bus = EventBus()


class EventHandler:
    """Base event handler class"""
    
    async def handle(self, event: Event):
        """Handle an event (to be overridden)"""
        raise NotImplementedError("Subclasses must implement handle method")


class MessageReceivedHandler(EventHandler):
    """Handler for MessageReceived events"""
    
    async def handle(self, event: Event):
        """Handle message received event"""
        # Logic to handle incoming messages
        # Could trigger bot response, notify agents, etc.
        pass


class MessageSentHandler(EventHandler):
    """Handler for MessageSent events"""
    
    async def handle(self, event: Event):
        """Handle message sent event"""
        # Logic to handle sent messages
        # Could update analytics, trigger webhooks, etc.
        pass


class ConversationCreatedHandler(EventHandler):
    """Handler for ConversationCreated events"""
    
    async def handle(self, event: Event):
        """Handle conversation created event"""
        # Logic to handle new conversations
        # Could assign to bot, notify agents, etc.
        pass


class ConversationAssignedHandler(EventHandler):
    """Handler for ConversationAssigned events"""
    
    async def handle(self, event: Event):
        """Handle conversation assigned event"""
        # Logic to handle conversation assignment
        # Could send notification to agent, etc.
        pass


class ConversationStatusChangedHandler(EventHandler):
    """Handler for ConversationStatusChanged events"""
    
    async def handle(self, event: Event):
        """Handle conversation status changed event"""
        # Logic to handle status changes
        # Could update analytics, etc.
        pass


class CustomerCreatedHandler(EventHandler):
    """Handler for CustomerCreated events"""
    
    async def handle(self, event: Event):
        """Handle customer created event"""
        # Logic to handle new customers
        pass


class CustomerUpdatedHandler(EventHandler):
    """Handler for CustomerUpdated events"""
    
    async def handle(self, event: Event):
        """Handle customer updated event"""
        # Logic to handle customer updates
        pass


# Helper functions to create and publish events
async def create_and_publish_event(event_type: str, data: Dict[str, Any], company_id: str):
    """Create and publish an event"""
    event = Event(
        event_type=event_type,
        data=data,
        timestamp=datetime.utcnow(),
        company_id=company_id
    )
    await event_bus.publish(event)
