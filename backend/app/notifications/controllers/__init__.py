"""Notification Controllers"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.notifications.services import NotificationService
from app.notifications.models import NotificationType, NotificationChannel
from app.notifications.websocket import handle_notification_websocket
from app.auth.dependencies import get_current_active_user
from app.users.models import User


router = APIRouter(prefix="/notifications", tags=["Notifications"])


# Request/Response Schemas
class NotificationResponse(BaseModel):
    """Notification response"""
    id: str
    user_id: str
    notification_type: str
    title: str
    message: str
    data: Optional[dict]
    is_read: bool
    read_at: Optional[str]
    created_at: str


class NotificationPreferenceResponse(BaseModel):
    """Notification preference response"""
    id: str
    user_id: str
    notification_type: str
    enabled: bool
    channel: str
    created_at: str
    updated_at: str


class CreateNotificationRequest(BaseModel):
    """Create notification request"""
    user_id: str
    notification_type: str
    title: str
    message: str
    data: Optional[dict]


class UpdatePreferenceRequest(BaseModel):
    """Update preference request"""
    notification_type: str
    enabled: bool
    channel: Optional[str]


# Notification endpoints
@router.get("", response_model=list[NotificationResponse])
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    unread_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's notifications"""
    notification_service = NotificationService(db)
    notifications = await notification_service.get_user_notifications(
        current_user.id,
        skip=skip,
        limit=limit,
        unread_only=unread_only
    )
    
    return [
        {
            "id": str(n.id),
            "user_id": str(n.user_id),
            "notification_type": n.notification_type.value,
            "title": n.title,
            "message": n.message,
            "data": n.data,
            "is_read": n.is_read,
            "read_at": n.read_at.isoformat() if n.read_at else None,
            "created_at": n.created_at.isoformat()
        }
        for n in notifications
    ]


@router.get("/unread-count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get unread notification count for current user"""
    notification_service = NotificationService(db)
    count = await notification_service.get_unread_count(current_user.id)
    return {"unread_count": count}


@router.post("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark notification as read"""
    notification_service = NotificationService(db)
    notification = await notification_service.mark_as_read(notification_id)
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return {"message": "Notification marked as read"}


@router.post("/read-all")
async def mark_all_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark all notifications as read for current user"""
    notification_service = NotificationService(db)
    count = await notification_service.mark_all_as_read(current_user.id)
    return {"message": f"Marked {count} notifications as read"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete notification"""
    from app.notifications.repositories import NotificationRepository
    notification_repo = NotificationRepository(db)
    
    notification = await notification_repo.get_by_id(notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    await notification_repo.delete(notification_id)
    return {"message": "Notification deleted"}


# Preference endpoints
@router.get("/preferences", response_model=list[NotificationPreferenceResponse])
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's notification preferences"""
    notification_service = NotificationService(db)
    preferences = await notification_service.get_preferences(current_user.id)
    
    return [
        {
            "id": str(p.id),
            "user_id": str(p.user_id),
            "notification_type": p.notification_type.value,
            "enabled": p.enabled,
            "channel": p.channel.value,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat()
        }
        for p in preferences
    ]


@router.put("/preferences")
async def update_preference(
    request: UpdatePreferenceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update notification preference"""
    try:
        notification_type = NotificationType(request.notification_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid notification type: {request.notification_type}"
        )
    
    channel = NotificationChannel.IN_APP
    if request.channel:
        try:
            channel = NotificationChannel(request.channel)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid channel: {request.channel}"
            )
    
    notification_service = NotificationService(db)
    preference = await notification_service.set_preference(
        current_user.id,
        notification_type,
        request.enabled,
        channel
    )
    
    return {
        "id": str(preference.id),
        "user_id": str(preference.user_id),
        "notification_type": preference.notification_type.value,
        "enabled": preference.enabled,
        "channel": preference.channel.value,
        "created_at": preference.created_at.isoformat(),
        "updated_at": preference.updated_at.isoformat()
    }


# WebSocket endpoint
@router.websocket("/ws")
async def websocket_notifications(
    websocket: WebSocket,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for real-time notifications"""
    from app.auth.dependencies import get_current_user_from_token
    from app.database import get_db_context
    
    # Verify token and get user
    async with get_db_context() as db_session:
        user = await get_current_user_from_token(token, db_session)
        if not user:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        await handle_notification_websocket(websocket, user.id, db_session)
