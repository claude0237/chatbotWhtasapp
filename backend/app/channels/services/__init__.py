"""Channel Abstraction Service"""
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from uuid import UUID
from datetime import datetime
from fastapi import Request


class ChannelProvider(ABC):
    """Abstract base class for channel providers"""
    
    @abstractmethod
    async def send_message(
        self,
        recipient: str,
        content: str,
        message_type: str = "TEXT",
        media_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send a message through the channel"""
        pass
    
    @abstractmethod
    async def receive_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """Process incoming webhook from the channel"""
        pass
    
    @abstractmethod
    async def verify_webhook(self, request: Request) -> bool:
        """Verify webhook signature"""
        pass
    
    @abstractmethod
    async def get_message_status(self, external_message_id: str) -> Dict[str, Any]:
        """Get status of a message"""
        pass
    
    @abstractmethod
    async def send_template(
        self,
        recipient: str,
        template_name: str,
        components: Optional[Dict[str, Any]] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        """Send a template message"""
        pass
    
    @abstractmethod
    async def send_media(
        self,
        recipient: str,
        media_url: str,
        media_type: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a media message (image, video, document, audio)"""
        pass


class ChannelFactory:
    """Factory for creating channel providers"""
    
    _providers: Dict[str, type] = {}
    
    @classmethod
    def register_provider(cls, channel_type: str, provider_class: type):
        """Register a channel provider"""
        cls._providers[channel_type] = provider_class
    
    @classmethod
    def create_provider(cls, channel_type: str, config: Dict[str, Any]) -> ChannelProvider:
        """Create a channel provider instance"""
        provider_class = cls._providers.get(channel_type)
        if not provider_class:
            raise ValueError(f"Unknown channel type: {channel_type}")
        
        return provider_class(config)
    
    @classmethod
    def get_available_channels(cls) -> List[str]:
        """Get list of available channel types"""
        return list(cls._providers.keys())


class ChannelService:
    """Service for managing channels"""
    
    def __init__(self, db):
        self.db = db
    
    async def create_channel(
        self,
        company_id: UUID,
        channel_type: str,
        name: str,
        configuration: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new channel"""
        from app.channels.models import Channel, ChannelConfiguration
        from app.channels.repositories import ChannelRepository
        
        channel_repo = ChannelRepository(self.db)
        
        channel = Channel(
            company_id=company_id,
            channel_type=channel_type,
            name=name,
            status="PENDING"
        )
        channel = await channel_repo.create(channel)
        
        # Create configuration entries
        if configuration:
            for key, value in configuration.items():
                config = ChannelConfiguration(
                    channel_id=channel.id,
                    key=key,
                    value=str(value),
                    is_encrypted=False
                )
                self.db.add(config)
            await self.db.commit()
        
        return {
            "id": str(channel.id),
            "channel_type": channel.channel_type.value,
            "name": channel.name,
            "status": channel.status.value
        }
    
    async def get_channel_provider(self, channel_id: UUID) -> ChannelProvider:
        """Get a channel provider instance for a channel"""
        from app.channels.models import Channel
        from app.channels.repositories import ChannelRepository, ChannelConfigurationRepository
        
        channel_repo = ChannelRepository(self.db)
        config_repo = ChannelConfigurationRepository(self.db)
        
        channel = await channel_repo.get_by_id(channel_id)
        if not channel:
            raise ValueError(f"Channel not found: {channel_id}")
        
        configurations = await config_repo.get_by_channel_id(channel_id)
        config_dict = {cfg.key: cfg.value for cfg in configurations}
        
        return ChannelFactory.create_provider(channel.channel_type.value, config_dict)
