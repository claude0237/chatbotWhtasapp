"""Bot Service"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.models import BotConfiguration, BotScenario, BotKeyword, BotType
from app.bot.repositories import BotConfigurationRepository, BotScenarioRepository, BotKeywordRepository
from app.knowledge.services import KnowledgeBaseService
from app.ml.engine import MLEngine
from app.products.bot_integration import ProductBotIntegration
from app.reservations.bot_integration import ReservationBotIntegration
import logging

logger = logging.getLogger(__name__)


class NativeBotEngine:
    """Native bot engine for processing messages based on rules and scenarios"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.config_repository = BotConfigurationRepository(db)
        self.scenario_repository = BotScenarioRepository(db)
        self.keyword_repository = BotKeywordRepository(db)
        self.knowledge_service = KnowledgeBaseService(db)
        self.ml_engine = MLEngine(db)
        self.product_integration = ProductBotIntegration(db)
        self.reservation_integration = ReservationBotIntegration(db)
    
    async def process_message(self, company_id: UUID, message: str, conversation_context: Optional[Dict[str, Any]] = None) -> str:
        """Process a message and return bot response"""
        config = await self.config_repository.get_active_configuration(company_id)
        
        if not config:
            logger.info(f"No bot configuration found for company {company_id}, returning unknown message")
            return await self.get_unknown_message(company_id)
        
        # If ML is enabled, use ML engine with fallback
        if config.ml_enabled and config.bot_type in [BotType.ML, BotType.HYBRID]:
            try:
                # Get conversation history if available
                conversation_history = conversation_context.get("history", []) if conversation_context else []
                
                # Try native response first for fallback
                native_response = None
                if config.bot_type == BotType.HYBRID:
                    native_response = await self._process_native_response(company_id, message, conversation_context)
                    logger.info(f"Company {company_id}: Generated native response for hybrid mode")
                
                # Process with ML engine and fallback
                logger.info(f"Company {company_id}: Processing with ML engine (provider: {config.ml_provider}, model: {config.ml_model})")
                ml_result = await self.ml_engine.process_with_fallback(
                    company_id=company_id,
                    message=message,
                    conversation_history=conversation_history,
                    native_response=native_response
                )
                
                # Log decision
                logger.info(
                    f"Company {company_id}: ML decision - strategy: {config.fallback_strategy}, "
                    f"used_ml: {ml_result.get('used_ml', False)}, "
                    f"confidence: {ml_result.get('confidence', 0)}"
                )
                
                return ml_result["response"]
            except Exception as e:
                logger.error(f"Company {company_id}: ML processing failed: {str(e)}")
                # Fallback to native processing
                logger.info(f"Company {company_id}: Falling back to native processing")
                return await self._process_native_response(company_id, message, conversation_context)
        
        # Native bot processing
        logger.info(f"Company {company_id}: Using native bot processing (bot_type: {config.bot_type})")
        return await self._process_native_response(company_id, message, conversation_context)
    
    async def _process_native_response(self, company_id: UUID, message: str, conversation_context: Optional[Dict[str, Any]] = None) -> str:
        """Process message using native bot logic"""
        # Try to match keyword first
        keyword_response = await self.match_keyword(company_id, message)
        if keyword_response:
            return keyword_response
        
        # Try to match scenario
        scenario_response = await self.execute_scenario(company_id, message, conversation_context)
        if scenario_response:
            return scenario_response
        
        # Search in knowledge base before returning unknown message
        knowledge_response = await self.search_knowledge_base(company_id, message)
        if knowledge_response:
            return knowledge_response
        
        # Check for reservation intent (before products)
        try:
            reservation_response = await self.reservation_integration.handle_reservation_query(
                company_id, message, conversation_context=conversation_context
            )
            if reservation_response:
                return reservation_response
        except Exception as e:
            logger.warning(f"Reservation integration failed: {e}")
        
        # Search in product catalog
        try:
            product_response = await self.product_integration.handle_product_query(company_id, message)
            if product_response:
                return product_response
        except Exception as e:
            logger.warning(f"Product search failed: {e}")
        
        # Return unknown message if no match
        return await self.get_unknown_message(company_id)
    
    async def match_keyword(self, company_id: UUID, message: str) -> Optional[str]:
        """Match message against keywords and return response"""
        config = await self.config_repository.get_active_configuration(company_id)
        if not config:
            return None
        
        keywords = await self.keyword_repository.get_by_bot_configuration_id(config.id)
        
        # Simple exact match
        message_lower = message.lower().strip()
        for keyword in keywords:
            if keyword.keyword.lower() == message_lower:
                return keyword.response
        
        # Partial match (if keyword is contained in message)
        for keyword in keywords:
            if keyword.keyword.lower() in message_lower:
                return keyword.response
        
        return None
    
    async def execute_scenario(self, company_id: UUID, message: str, conversation_context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Execute a scenario based on trigger keyword"""
        config = await self.config_repository.get_active_configuration(company_id)
        if not config:
            return None
        
        # Check if message matches a trigger keyword
        scenarios = await self.scenario_repository.get_active_scenarios(config.id)
        message_lower = message.lower().strip()
        
        for scenario in scenarios:
            if scenario.trigger_keyword.lower() in message_lower:
                # Execute scenario steps
                if scenario.steps and isinstance(scenario.steps, list):
                    # Return first step response (simplified)
                    first_step = scenario.steps[0] if scenario.steps else None
                    if first_step and isinstance(first_step, dict):
                        return first_step.get('response', '')
        
        return None
    
    async def get_welcome_message(self, company_id: UUID) -> str:
        """Get welcome message for the bot"""
        config = await self.config_repository.get_active_configuration(company_id)
        if config and config.welcome_message:
            return config.welcome_message
        return "Hello! How can I help you today?"
    
    async def get_away_message(self, company_id: UUID) -> str:
        """Get away message for the bot"""
        config = await self.config_repository.get_active_configuration(company_id)
        if config and config.away_message:
            return config.away_message
        return "I'm currently away. Please leave a message and I'll get back to you soon."
    
    async def get_unknown_message(self, company_id: UUID) -> str:
        """Get unknown message for the bot"""
        config = await self.config_repository.get_active_configuration(company_id)
        if config and config.unknown_message:
            return config.unknown_message
        return "I'm not sure how to help with that. Would you like to speak with a human agent?"
    
    async def get_closing_message(self, company_id: UUID) -> str:
        """Get closing message for the bot"""
        config = await self.config_repository.get_active_configuration(company_id)
        if config and config.closing_message:
            return config.closing_message
        return "Thank you for chatting with us. Have a great day!"
    
    async def search_knowledge_base(self, company_id: UUID, query: str) -> Optional[str]:
        """Search knowledge base for relevant information"""
        try:
            results = await self.knowledge_service.search(company_id, query, skip=0, limit=1)
            if results and len(results) > 0:
                # Return the content of the first matching entry
                return results[0].content
        except Exception as e:
            # Log error but don't fail the entire bot response
            print(f"Error searching knowledge base: {e}")
        return None


class BotConfigurationService:
    """Service for BotConfiguration operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = BotConfigurationRepository(db)
        self.scenario_repository = BotScenarioRepository(db)
        self.keyword_repository = BotKeywordRepository(db)
    
    async def create_configuration(
        self,
        company_id: UUID,
        bot_type: BotType,
        name: str,
        welcome_message: Optional[str] = None,
        away_message: Optional[str] = None,
        closing_message: Optional[str] = None,
        unknown_message: Optional[str] = None,
        language: str = "en",
        timezone: str = "UTC",
        avatar_url: Optional[str] = None,
        native_rules: Optional[Dict[str, Any]] = None,
        followup_timeout_minutes: int = 60,
        followup_max_retries: int = 3,
        ml_enabled: Optional[bool] = None,
        ml_provider: Optional[str] = None,
        ml_model: Optional[str] = None,
        ml_temperature: Optional[str] = None,
        ml_max_tokens: Optional[int] = None,
        fallback_strategy: Optional[str] = None,
        confidence_threshold: Optional[str] = None
    ) -> BotConfiguration:
        """Create a new bot configuration"""
        from app.bot.models import MLProvider, FallbackStrategy
        
        config = BotConfiguration(
            company_id=company_id,
            bot_type=bot_type,
            name=name,
            welcome_message=welcome_message,
            away_message=away_message,
            closing_message=closing_message,
            unknown_message=unknown_message,
            language=language,
            timezone=timezone,
            avatar_url=avatar_url,
            native_rules=native_rules,
            followup_timeout_minutes=followup_timeout_minutes,
            followup_max_retries=followup_max_retries,
            ml_enabled=ml_enabled if ml_enabled is not None else (bot_type in [BotType.ML, BotType.HYBRID]),
            ml_provider=MLProvider(ml_provider) if ml_provider else None,
            ml_model=ml_model,
            ml_temperature=ml_temperature,
            ml_max_tokens=ml_max_tokens,
            fallback_strategy=FallbackStrategy(fallback_strategy) if fallback_strategy else None,
            confidence_threshold=confidence_threshold
        )
        return await self.repository.create(config)
    
    async def update_configuration(
        self,
        config_id: UUID,
        name: Optional[str] = None,
        welcome_message: Optional[str] = None,
        away_message: Optional[str] = None,
        closing_message: Optional[str] = None,
        unknown_message: Optional[str] = None,
        language: Optional[str] = None,
        timezone: Optional[str] = None,
        avatar_url: Optional[str] = None,
        native_rules: Optional[Dict[str, Any]] = None,
        bot_type: Optional[BotType] = None,
        followup_timeout_minutes: Optional[int] = None,
        followup_max_retries: Optional[int] = None,
        ml_enabled: Optional[bool] = None,
        ml_provider: Optional[str] = None,
        ml_model: Optional[str] = None,
        ml_temperature: Optional[str] = None,
        ml_max_tokens: Optional[int] = None,
        fallback_strategy: Optional[str] = None,
        confidence_threshold: Optional[str] = None
    ) -> Optional[BotConfiguration]:
        """Update bot configuration"""
        from app.bot.models import MLProvider, FallbackStrategy
        
        config = await self.repository.get_by_id(config_id)
        if config:
            if name is not None:
                config.name = name
            if welcome_message is not None:
                config.welcome_message = welcome_message
            if away_message is not None:
                config.away_message = away_message
            if closing_message is not None:
                config.closing_message = closing_message
            if unknown_message is not None:
                config.unknown_message = unknown_message
            if language is not None:
                config.language = language
            if timezone is not None:
                config.timezone = timezone
            if avatar_url is not None:
                config.avatar_url = avatar_url
            if native_rules is not None:
                config.native_rules = native_rules
            if bot_type is not None:
                config.bot_type = bot_type
            if followup_timeout_minutes is not None:
                config.followup_timeout_minutes = followup_timeout_minutes
            if followup_max_retries is not None:
                config.followup_max_retries = followup_max_retries
            if ml_enabled is not None:
                config.ml_enabled = ml_enabled
            if ml_provider is not None and ml_provider:
                config.ml_provider = MLProvider(ml_provider)
            if ml_model is not None:
                config.ml_model = ml_model
            if ml_temperature is not None:
                config.ml_temperature = ml_temperature
            if ml_max_tokens is not None:
                config.ml_max_tokens = ml_max_tokens
            if fallback_strategy is not None and fallback_strategy:
                config.fallback_strategy = FallbackStrategy(fallback_strategy)
            if confidence_threshold is not None:
                config.confidence_threshold = confidence_threshold
            return await self.repository.update(config)
        return None
    
    async def get_active_configuration(self, company_id: UUID) -> Optional[BotConfiguration]:
        """Get active bot configuration for a company"""
        return await self.repository.get_active_configuration(company_id)
    
    async def get_by_id(self, config_id: UUID) -> Optional[BotConfiguration]:
        """Get bot configuration by ID"""
        return await self.repository.get_by_id(config_id)
