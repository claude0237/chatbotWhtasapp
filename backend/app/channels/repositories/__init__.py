"""Channel Repository"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from app.channels.models import Channel, ChannelConfiguration, ChannelCredential, ChannelMessage, ChannelWebhookLog


class ChannelRepository:
    """Repository for channel operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, channel: Channel) -> Channel:
        """Create a new channel"""
        self.db.add(channel)
        await self.db.commit()
        await self.db.refresh(channel)
        return channel
    
    async def get_by_id(self, channel_id: UUID) -> Optional[Channel]:
        """Get channel by ID"""
        result = await self.db.execute(
            select(Channel).where(Channel.id == channel_id)
        )
        return result.scalars().first()
    
    async def get_by_company_id(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Channel]:
        """Get channels by company ID"""
        result = await self.db.execute(
            select(Channel)
            .where(Channel.company_id == company_id)
            .order_by(desc(Channel.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_type(
        self,
        company_id: UUID,
        channel_type: str
    ) -> Optional[Channel]:
        """Get channel by company and type"""
        result = await self.db.execute(
            select(Channel).where(
                and_(
                    Channel.company_id == company_id,
                    Channel.channel_type == channel_type
                )
            )
        )
        return result.scalars().first()
    
    async def update(self, channel: Channel) -> Channel:
        """Update channel"""
        await self.db.commit()
        await self.db.refresh(channel)
        return channel
    
    async def get_by_phone_number_id(self, phone_number_id: str) -> Optional[Channel]:
        """Get WhatsApp channel by Meta phone_number_id stored in configurations"""
        result = await self.db.execute(
            select(Channel)
            .join(ChannelConfiguration, ChannelConfiguration.channel_id == Channel.id)
            .where(
                and_(
                    ChannelConfiguration.key == "phone_number_id",
                    ChannelConfiguration.value == phone_number_id
                )
            )
        )
        return result.scalars().first()

    async def delete(self, channel_id: UUID):
        """Delete channel"""
        channel = await self.get_by_id(channel_id)
        if channel:
            await self.db.delete(channel)
            await self.db.commit()


class ChannelConfigurationRepository:
    """Repository for channel configuration operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, configuration: ChannelConfiguration) -> ChannelConfiguration:
        """Create a new configuration"""
        self.db.add(configuration)
        await self.db.commit()
        await self.db.refresh(configuration)
        return configuration
    
    async def get_by_channel_id(
        self,
        channel_id: UUID
    ) -> List[ChannelConfiguration]:
        """Get configurations by channel ID"""
        result = await self.db.execute(
            select(ChannelConfiguration).where(ChannelConfiguration.channel_id == channel_id)
        )
        return result.scalars().all()
    
    async def get_by_key(
        self,
        channel_id: UUID,
        key: str
    ) -> Optional[ChannelConfiguration]:
        """Get configuration by channel and key"""
        result = await self.db.execute(
            select(ChannelConfiguration).where(
                and_(
                    ChannelConfiguration.channel_id == channel_id,
                    ChannelConfiguration.key == key
                )
            )
        )
        return result.scalars().first()
    
    async def update(self, configuration: ChannelConfiguration) -> ChannelConfiguration:
        """Update configuration"""
        await self.db.commit()
        await self.db.refresh(configuration)
        return configuration
    
    async def delete(self, configuration_id: UUID):
        """Delete configuration"""
        configuration = await self.db.execute(
            select(ChannelConfiguration).where(ChannelConfiguration.id == configuration_id)
        )
        configuration = configuration.scalars().first()
        if configuration:
            await self.db.delete(configuration)
            await self.db.commit()


class ChannelCredentialRepository:
    """Repository for channel credential operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, credential: ChannelCredential) -> ChannelCredential:
        """Create a new credential"""
        self.db.add(credential)
        await self.db.commit()
        await self.db.refresh(credential)
        return credential
    
    async def get_by_channel_id(
        self,
        channel_id: UUID
    ) -> List[ChannelCredential]:
        """Get credentials by channel ID"""
        result = await self.db.execute(
            select(ChannelCredential).where(ChannelCredential.channel_id == channel_id)
        )
        return result.scalars().all()
    
    async def get_by_type(
        self,
        channel_id: UUID,
        credential_type: str
    ) -> Optional[ChannelCredential]:
        """Get credential by channel and type"""
        result = await self.db.execute(
            select(ChannelCredential).where(
                and_(
                    ChannelCredential.channel_id == channel_id,
                    ChannelCredential.credential_type == credential_type
                )
            )
        )
        return result.scalars().first()
    
    async def update(self, credential: ChannelCredential) -> ChannelCredential:
        """Update credential"""
        await self.db.commit()
        await self.db.refresh(credential)
        return credential
    
    async def delete(self, credential_id: UUID):
        """Delete credential"""
        credential = await self.db.execute(
            select(ChannelCredential).where(ChannelCredential.id == credential_id)
        )
        credential = credential.scalars().first()
        if credential:
            await self.db.delete(credential)
            await self.db.commit()


class ChannelMessageRepository:
    """Repository for channel message operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, message: ChannelMessage) -> ChannelMessage:
        """Create a new message"""
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message
    
    async def get_by_id(self, message_id: UUID) -> Optional[ChannelMessage]:
        """Get message by ID"""
        result = await self.db.execute(
            select(ChannelMessage).where(ChannelMessage.id == message_id)
        )
        return result.scalars().first()
    
    async def get_by_external_id(self, external_message_id: str) -> Optional[ChannelMessage]:
        """Get message by external message ID"""
        result = await self.db.execute(
            select(ChannelMessage).where(ChannelMessage.external_message_id == external_message_id)
        )
        return result.scalars().first()
    
    async def get_by_channel_id(
        self,
        channel_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ChannelMessage]:
        """Get messages by channel ID"""
        result = await self.db.execute(
            select(ChannelMessage)
            .where(ChannelMessage.channel_id == channel_id)
            .order_by(desc(ChannelMessage.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_company_id(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ChannelMessage]:
        """Get messages by company ID"""
        result = await self.db.execute(
            select(ChannelMessage)
            .where(ChannelMessage.company_id == company_id)
            .order_by(desc(ChannelMessage.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def update(self, message: ChannelMessage) -> ChannelMessage:
        """Update message"""
        await self.db.commit()
        await self.db.refresh(message)
        return message
    
    async def delete(self, message_id: UUID):
        """Delete message"""
        message = await self.get_by_id(message_id)
        if message:
            await self.db.delete(message)
            await self.db.commit()


class ChannelWebhookLogRepository:
    """Repository for channel webhook log operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, webhook_log: ChannelWebhookLog) -> ChannelWebhookLog:
        """Create a new webhook log"""
        self.db.add(webhook_log)
        await self.db.commit()
        await self.db.refresh(webhook_log)
        return webhook_log
    
    async def get_by_id(self, webhook_log_id: UUID) -> Optional[ChannelWebhookLog]:
        """Get webhook log by ID"""
        result = await self.db.execute(
            select(ChannelWebhookLog).where(ChannelWebhookLog.id == webhook_log_id)
        )
        return result.scalars().first()
    
    async def get_by_channel_id(
        self,
        channel_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ChannelWebhookLog]:
        """Get webhook logs by channel ID"""
        result = await self.db.execute(
            select(ChannelWebhookLog)
            .where(ChannelWebhookLog.channel_id == channel_id)
            .order_by(desc(ChannelWebhookLog.received_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def mark_as_processed(self, webhook_log_id: UUID):
        """Mark webhook log as processed"""
        webhook_log = await self.get_by_id(webhook_log_id)
        if webhook_log:
            webhook_log.processing_status = "PROCESSED"
            webhook_log.processed_at = datetime.utcnow()
            await self.db.commit()
    
    async def mark_as_failed(self, webhook_log_id: UUID, error_message: str):
        """Mark webhook log as failed"""
        webhook_log = await self.get_by_id(webhook_log_id)
        if webhook_log:
            webhook_log.processing_status = "FAILED"
            webhook_log.error_message = error_message
            webhook_log.processed_at = datetime.utcnow()
            await self.db.commit()
