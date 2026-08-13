"""Bot Repository"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.models import BotConfiguration, BotScenario, BotKeyword, MLModel, BotConversationState
from app.cache import get_cache_service


class BotConfigurationRepository:
    """Repository for BotConfiguration model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, config: BotConfiguration) -> BotConfiguration:
        """Create a new bot configuration"""
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        return config
    
    async def get_by_id(self, config_id: UUID) -> Optional[BotConfiguration]:
        """Get bot configuration by ID"""
        result = await self.db.execute(
            select(BotConfiguration).where(BotConfiguration.id == config_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_company_id(self, company_id: UUID, use_cache: bool = False) -> Optional[BotConfiguration]:
        """Get bot configuration by company ID"""
        # Cache disabled for SQLAlchemy objects to avoid serialization issues
        result = await self.db.execute(
            select(BotConfiguration).where(BotConfiguration.company_id == company_id)
        )
        config = result.scalar_one_or_none()
        
        return config
    
    async def get_active_configuration(self, company_id: UUID) -> Optional[BotConfiguration]:
        """Get active bot configuration for a company"""
        return await self.get_by_company_id(company_id)
    
    async def update(self, config: BotConfiguration) -> BotConfiguration:
        """Update bot configuration"""
        await self.db.commit()
        await self.db.refresh(config)
        
        # Invalidate cache
        cache = await get_cache_service()
        await cache.delete("bot_config", config.company_id)
        
        return config
    
    async def delete(self, config_id: UUID) -> bool:
        """Delete bot configuration by ID"""
        result = await self.db.execute(
            select(BotConfiguration).where(BotConfiguration.id == config_id)
        )
        config = result.scalar_one_or_none()
        if config:
            await self.db.delete(config)
            await self.db.commit()
            
            # Invalidate cache
            cache = await get_cache_service()
            await cache.delete("bot_config", config.company_id)
            
            return True
        return False


class BotScenarioRepository:
    """Repository for BotScenario model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, scenario: BotScenario) -> BotScenario:
        """Create a new bot scenario"""
        self.db.add(scenario)
        await self.db.commit()
        await self.db.refresh(scenario)
        return scenario
    
    async def get_by_id(self, scenario_id: UUID) -> Optional[BotScenario]:
        """Get bot scenario by ID"""
        result = await self.db.execute(
            select(BotScenario).where(BotScenario.id == scenario_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_bot_configuration_id(self, bot_configuration_id: UUID) -> List[BotScenario]:
        """Get scenarios by bot configuration ID"""
        result = await self.db.execute(
            select(BotScenario)
            .where(BotScenario.bot_configuration_id == bot_configuration_id)
            .order_by(BotScenario.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_by_trigger_keyword(self, bot_configuration_id: UUID, trigger_keyword: str, use_cache: bool = False) -> Optional[BotScenario]:
        """Get scenario by trigger keyword"""
        # Cache disabled for SQLAlchemy objects to avoid serialization issues
        result = await self.db.execute(
            select(BotScenario).where(
                and_(
                    BotScenario.bot_configuration_id == bot_configuration_id,
                    BotScenario.trigger_keyword == trigger_keyword,
                    BotScenario.is_active == True
                )
            )
        )
        scenario = result.scalar_one_or_none()
        
        return scenario
    
    async def get_active_scenarios(self, bot_configuration_id: UUID) -> List[BotScenario]:
        """Get active scenarios for a bot configuration"""
        result = await self.db.execute(
            select(BotScenario)
            .where(
                and_(
                    BotScenario.bot_configuration_id == bot_configuration_id,
                    BotScenario.is_active == True
                )
            )
            .order_by(BotScenario.created_at.desc())
        )
        return result.scalars().all()
    
    async def update(self, scenario: BotScenario) -> BotScenario:
        """Update bot scenario"""
        await self.db.commit()
        await self.db.refresh(scenario)
        
        # Invalidate cache for this scenario's trigger keyword
        cache = await get_cache_service()
        await cache.delete("scenario_trigger", scenario.bot_configuration_id, scenario.trigger_keyword.upper())
        
        return scenario
    
    async def delete(self, scenario_id: UUID) -> bool:
        """Delete bot scenario by ID"""
        result = await self.db.execute(
            select(BotScenario).where(BotScenario.id == scenario_id)
        )
        scenario = result.scalar_one_or_none()
        if scenario:
            await self.db.delete(scenario)
            await self.db.commit()
            
            # Invalidate cache for this scenario's trigger keyword
            cache = await get_cache_service()
            await cache.delete("scenario_trigger", scenario.bot_configuration_id, scenario.trigger_keyword.upper())
            
            return True
        return False


class BotKeywordRepository:
    """Repository for BotKeyword model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, keyword: BotKeyword) -> BotKeyword:
        """Create a new bot keyword"""
        self.db.add(keyword)
        await self.db.commit()
        await self.db.refresh(keyword)
        return keyword
    
    async def get_by_id(self, keyword_id: UUID) -> Optional[BotKeyword]:
        """Get bot keyword by ID"""
        result = await self.db.execute(
            select(BotKeyword).where(BotKeyword.id == keyword_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_bot_configuration_id(self, bot_configuration_id: UUID) -> List[BotKeyword]:
        """Get keywords by bot configuration ID"""
        result = await self.db.execute(
            select(BotKeyword)
            .where(BotKeyword.bot_configuration_id == bot_configuration_id)
            .order_by(BotKeyword.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_by_keyword(self, bot_configuration_id: UUID, keyword: str, use_cache: bool = False) -> Optional[BotKeyword]:
        """Get keyword by keyword text for a bot configuration"""
        # Cache disabled for SQLAlchemy objects to avoid serialization issues
        result = await self.db.execute(
            select(BotKeyword).where(
                and_(
                    BotKeyword.bot_configuration_id == bot_configuration_id,
                    BotKeyword.keyword == keyword
                )
            )
        )
        kw = result.scalar_one_or_none()
        
        return kw
    
    async def get_by_category(self, bot_configuration_id: UUID, category: str) -> List[BotKeyword]:
        """Get keywords by category for a bot configuration"""
        result = await self.db.execute(
            select(BotKeyword)
            .where(
                and_(
                    BotKeyword.bot_configuration_id == bot_configuration_id,
                    BotKeyword.category == category
                )
            )
            .order_by(BotKeyword.created_at.desc())
        )
        return result.scalars().all()
    
    async def update(self, keyword: BotKeyword) -> BotKeyword:
        """Update bot keyword"""
        await self.db.commit()
        await self.db.refresh(keyword)
        
        # Invalidate cache for this keyword
        cache = await get_cache_service()
        await cache.delete("keyword", keyword.bot_configuration_id, keyword.keyword.upper())
        
        return keyword
    
    async def delete(self, keyword_id: UUID) -> bool:
        """Delete bot keyword by ID"""
        result = await self.db.execute(
            select(BotKeyword).where(BotKeyword.id == keyword_id)
        )
        keyword = result.scalar_one_or_none()
        if keyword:
            await self.db.delete(keyword)
            await self.db.commit()
            
            # Invalidate cache for this keyword
            cache = await get_cache_service()
            await cache.delete("keyword", keyword.bot_configuration_id, keyword.keyword.upper())
            
            return True
        return False


class MLModelRepository:
    """Repository for MLModel model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, model: MLModel) -> MLModel:
        """Create a new ML model"""
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return model
    
    async def get_by_id(self, model_id: UUID) -> Optional[MLModel]:
        """Get ML model by ID"""
        result = await self.db.execute(
            select(MLModel).where(MLModel.id == model_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_company_id(self, company_id: UUID, skip: int = 0, limit: int = 100) -> List[MLModel]:
        """Get ML models by company ID with pagination"""
        result = await self.db.execute(
            select(MLModel)
            .where(MLModel.company_id == company_id)
            .order_by(MLModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_active_models(self, company_id: UUID) -> List[MLModel]:
        """Get active ML models for a company"""
        result = await self.db.execute(
            select(MLModel)
            .where(
                and_(
                    MLModel.company_id == company_id,
                    MLModel.is_active == True
                )
            )
            .order_by(MLModel.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_by_type(self, company_id: UUID, model_type: str) -> List[MLModel]:
        """Get ML models by type for a company"""
        result = await self.db.execute(
            select(MLModel)
            .where(
                and_(
                    MLModel.company_id == company_id,
                    MLModel.model_type == model_type
                )
            )
            .order_by(MLModel.created_at.desc())
        )
        return result.scalars().all()
    
    async def update(self, model: MLModel) -> MLModel:
        """Update ML model"""
        await self.db.commit()
        await self.db.refresh(model)
        return model
    
    async def delete(self, model_id: UUID) -> bool:
        """Delete ML model by ID"""
        model = await self.get_by_id(model_id)
        if model:
            await self.db.delete(model)
            await self.db.commit()
            return True
        return False


class BotConversationStateRepository:
    """Repository for BotConversationState — tracks per-contact scenario progress"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active(self, company_id: UUID, phone_number: str) -> Optional[BotConversationState]:
        """Get the active scenario state for a contact"""
        result = await self.db.execute(
            select(BotConversationState)
            .options(selectinload(BotConversationState.scenario))
            .where(
                and_(
                    BotConversationState.company_id == company_id,
                    BotConversationState.phone_number == phone_number
                )
            )
        )
        return result.scalar_one_or_none()

    async def create(self, state: BotConversationState) -> BotConversationState:
        """Start a new conversation state"""
        self.db.add(state)
        await self.db.commit()
        await self.db.refresh(state)
        return state

    async def update(self, state: BotConversationState) -> BotConversationState:
        """Advance to next step"""
        await self.db.commit()
        await self.db.refresh(state)
        return state

    async def delete(self, state: BotConversationState):
        """End (delete) a completed conversation state"""
        await self.db.delete(state)
        await self.db.commit()
