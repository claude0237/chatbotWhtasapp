"""Notification Services"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.notifications.models import Notification, NotificationPreference, NotificationType, NotificationChannel
from app.notifications.repositories import NotificationRepository, NotificationPreferenceRepository
from app.users.repositories import UserRepository
from app.users.models import UserRoleEnum as UserRole


class NotificationService:
    """Service for managing notifications"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_repository = NotificationRepository(db)
        self.preference_repository = NotificationPreferenceRepository(db)
        self.user_repository = UserRepository(db)
    
    async def create_notification(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """Create a new notification"""
        # Check user's notification preference
        preference = await self.preference_repository.get_by_user_and_type(
            user_id,
            notification_type
        )
        
        # If preference exists and is disabled, don't create notification
        if preference and not preference.enabled:
            return None
        
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            data=data
        )
        
        return await self.notification_repository.create(notification)
    
    async def send_to_user(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """Send notification to a specific user"""
        return await self.create_notification(
            user_id,
            notification_type,
            title,
            message,
            data
        )
    
    async def send_to_role(
        self,
        company_id: UUID,
        role: UserRole,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> List[Notification]:
        """Send notification to all users with a specific role in a company"""
        users = await self.user_repository.get_by_company_and_role(company_id, role)
        
        notifications = []
        for user in users:
            notification = await self.create_notification(
                user.id,
                notification_type,
                title,
                message,
                data
            )
            if notification:
                notifications.append(notification)
        
        return notifications
    
    async def mark_as_read(self, notification_id: UUID) -> Optional[Notification]:
        """Mark notification as read"""
        return await self.notification_repository.mark_as_read(notification_id)
    
    async def mark_all_as_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user"""
        return await self.notification_repository.mark_all_as_read(user_id)
    
    async def get_user_notifications(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications for a user"""
        return await self.notification_repository.get_by_user_id(
            user_id,
            skip=skip,
            limit=limit,
            unread_only=unread_only
        )
    
    async def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications for a user"""
        return await self.notification_repository.get_unread_count(user_id)
    
    async def set_preference(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        enabled: bool,
        channel: NotificationChannel = NotificationChannel.IN_APP
    ) -> NotificationPreference:
        """Set notification preference for a user"""
        preference = await self.preference_repository.get_by_user_and_type(
            user_id,
            notification_type
        )
        
        if preference:
            preference.enabled = enabled
            preference.channel = channel
            return await self.preference_repository.update(preference)
        else:
            new_preference = NotificationPreference(
                user_id=user_id,
                notification_type=notification_type,
                enabled=enabled,
                channel=channel
            )
            return await self.preference_repository.create(new_preference)
    
    async def get_preferences(self, user_id: UUID) -> List[NotificationPreference]:
        """Get all notification preferences for a user"""
        # Get all preferences for user
        preferences = []
        for notification_type in NotificationType:
            preference = await self.preference_repository.get_by_user_and_type(
                user_id,
                notification_type
            )
            if preference:
                preferences.append(preference)
            else:
                # Create default preference
                default_preference = NotificationPreference(
                    user_id=user_id,
                    notification_type=notification_type,
                    enabled=True,
                    channel=NotificationChannel.IN_APP
                )
                preferences.append(await self.preference_repository.create(default_preference))
        
        return preferences
