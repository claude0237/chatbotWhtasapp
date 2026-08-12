"""WebSocket for real-time notifications"""
from typing import Dict, Set
from uuid import UUID
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.notifications.models import Notification


class NotificationConnectionManager:
    """Manager for WebSocket notification connections"""
    
    def __init__(self):
        # user_id -> set of WebSocket connections
        self.active_connections: Dict[UUID, Set[WebSocket]] = {}
    
    async def connect(self, user_id: UUID, websocket: WebSocket):
        """Connect a user's WebSocket"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
    
    def disconnect(self, user_id: UUID, websocket: WebSocket):
        """Disconnect a user's WebSocket"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_notification(self, user_id: UUID, notification: Notification):
        """Send notification to all connections for a user"""
        if user_id in self.active_connections:
            notification_data = {
                "id": str(notification.id),
                "user_id": str(notification.user_id),
                "notification_type": notification.notification_type.value,
                "title": notification.title,
                "message": notification.message,
                "data": notification.data,
                "is_read": notification.is_read,
                "read_at": notification.read_at.isoformat() if notification.read_at else None,
                "created_at": notification.created_at.isoformat()
            }
            
            # Send to all connections for this user
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(notification_data)
                except Exception:
                    disconnected.add(connection)
            
            # Clean up disconnected connections
            for connection in disconnected:
                self.disconnect(user_id, connection)
    
    async def broadcast_to_role(self, user_ids: Set[UUID], notification: Notification):
        """Broadcast notification to multiple users (e.g., by role)"""
        tasks = []
        for user_id in user_ids:
            tasks.append(self.send_notification(user_id, notification))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


# Global connection manager
notification_manager = NotificationConnectionManager()


async def handle_notification_websocket(
    websocket: WebSocket,
    user_id: UUID,
    db: AsyncSession
):
    """Handle WebSocket connection for notifications"""
    await notification_manager.connect(user_id, websocket)
    
    try:
        # Send unread count on connection
        from app.notifications.services import NotificationService
        notification_service = NotificationService(db)
        unread_count = await notification_service.get_unread_count(user_id)
        
        await websocket.send_json({
            "type": "unread_count",
            "count": unread_count
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_json()
            
            # Handle client requests (e.g., mark as read)
            if data.get("type") == "mark_as_read":
                notification_id = data.get("notification_id")
                if notification_id:
                    await notification_service.mark_as_read(notification_id)
                    
                    # Send updated unread count
                    new_count = await notification_service.get_unread_count(user_id)
                    await websocket.send_json({
                        "type": "unread_count",
                        "count": new_count
                    })
            
            elif data.get("type") == "mark_all_as_read":
                await notification_service.mark_all_as_read(user_id)
                
                # Send updated unread count
                new_count = await notification_service.get_unread_count(user_id)
                await websocket.send_json({
                    "type": "unread_count",
                    "count": new_count
                })
    
    except WebSocketDisconnect:
        notification_manager.disconnect(user_id, websocket)
    except Exception as e:
        notification_manager.disconnect(user_id, websocket)
        raise e
