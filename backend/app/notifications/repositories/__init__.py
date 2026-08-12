"""Notification Repositories"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.notifications.models import Notification, NotificationPreference, NotificationType


class NotificationRepository:
    """Repository for Notification model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, notification: Notification) -> Notification:
        """Create a new notification"""
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification
    
    async def get_by_id(self, notification_id: UUID) -> Optional[Notification]:
        """Get notification by ID"""
        result = await self.db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_id(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications for a user with pagination"""
        query = select(Notification).where(Notification.user_id == user_id)
        
        if unread_only:
            query = query.where(Notification.is_read == False)
        
        query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications for a user"""
        result = await self.db.execute(
            select(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            )
        )
        return len(result.scalars().all())
    
    async def mark_as_read(self, notification_id: UUID) -> Optional[Notification]:
        """Mark notification as read"""
        notification = await self.get_by_id(notification_id)
        if notification:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(notification)
        return notification
    
    async def mark_all_as_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user"""
        result = await self.db.execute(
            select(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            )
        )
        notifications = result.scalars().all()
        
        count = 0
        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            count += 1
        
        await self.db.commit()
        return count
    
    async def delete(self, notification_id: UUID) -> bool:
        """Delete notification by ID"""
        notification = await self.get_by_id(notification_id)
        if notification:
            await self.db.delete(notification)
            await self.db.commit()
            return True
        return False


class NotificationPreferenceRepository:
    """Repository for NotificationPreference model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, preference: NotificationPreference) -> NotificationPreference:
        """Create a new notification preference"""
        self.db.add(preference)
        await self.db.commit()
        await self.db.refresh(preference)
        return preference
    
    async def get_by_id(self, preference_id: UUID) -> Optional[NotificationPreference]:
        """Get preference by ID"""
        result = await self.db.execute(
            select(NotificationPreference).where(NotificationPreference.id == preference_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_id(self, user_id: UUID) -> Optional[NotificationPreference]:
        """Get preference by user ID"""
        result = await self.db.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_and_type(
        self,
        user_id: UUID,
        notification_type: NotificationType
    ) -> Optional[NotificationPreference]:
        """Get preference by user ID and notification type"""
        result = await self.db.execute(
            select(NotificationPreference).where(
                and_(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.notification_type == notification_type
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def update(self, preference: NotificationPreference) -> NotificationPreference:
        """Update notification preference"""
        await self.db.commit()
        await self.db.refresh(preference)
        return preference
    
    async def delete(self, preference_id: UUID) -> bool:
        """Delete preference by ID"""
        preference = await self.get_by_id(preference_id)
        if preference:
            await self.db.delete(preference)
            await self.db.commit()
            return True
        return False
