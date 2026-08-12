"""ML Engine for orchestrating RAG and LLM"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.ml.rag import RAGEngine
from app.ml.llm import get_llm_provider
from app.bot.repositories import BotConfigurationRepository
from app.ml.models import MLProviderConfig
from app.config import settings


class MLEngine:
    """ML Engine for orchestrating RAG and LLM generation"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.config_repository = BotConfigurationRepository(db)
        self.rag_engine = None
        self.llm_provider = None
    
    async def _initialize_for_company(self, company_id: UUID):
        """Initialize RAG and LLM for a company based on configuration"""
        config = await self.config_repository.get_active_configuration(company_id)
        
        if not config or not config.ml_enabled:
            raise RuntimeError("ML not enabled for this company")
        
        # Initialize LLM provider
        if config.ml_provider:
            provider_type = config.ml_provider.value if hasattr(config.ml_provider, 'value') else str(config.ml_provider)
            # Get superadmin config for this provider type
            result = await self.db.execute(
                select(MLProviderConfig).where(
                    MLProviderConfig.provider_type == config.ml_provider,
                    MLProviderConfig.is_active == True
                )
            )
            active_config = result.scalar_one_or_none()
            
            if active_config:
                # Use superadmin config for this provider
                self.llm_provider = get_llm_provider(provider_type, config=active_config)
            else:
                # Fallback to .env if no superadmin config for this provider
                self.llm_provider = get_llm_provider(provider_type)
        else:
            # Try to get active provider from superadmin config
            result = await self.db.execute(
                select(MLProviderConfig).where(MLProviderConfig.is_active == True)
            )
            active_config = result.scalar_one_or_none()
            
            if active_config:
                # Use superadmin config
                provider_type = active_config.provider_type.value
                self.llm_provider = get_llm_provider(provider_type, config=active_config)
            else:
                # Fallback to .env
                provider_type = settings.ml_default_provider
                self.llm_provider = get_llm_provider(provider_type)
        
        # Initialize RAG engine
        self.rag_engine = RAGEngine(self.db, self.llm_provider)
    
    async def process_message(
        self,
        company_id: UUID,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        confidence_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Process message using ML engine with RAG"""
        # Initialize for company
        await self._initialize_for_company(company_id)
        
        config = await self.config_repository.get_active_configuration(company_id)
        
        # Get ML parameters from arguments or fallback to config
        temp = temperature if temperature is not None else (float(config.ml_temperature) if config.ml_temperature else 0.7)
        tokens = max_tokens if max_tokens is not None else (config.ml_max_tokens if config.ml_max_tokens else 500)
        threshold = confidence_threshold if confidence_threshold is not None else (float(config.confidence_threshold) if config.confidence_threshold else 0.5)
        
        # Generate response with RAG
        if conversation_history:
            result = await self.rag_engine.generate_with_history(
                company_id=company_id,
                query=message,
                conversation_history=conversation_history,
                top_k=3,
                threshold=threshold,
                temperature=temp,
                max_tokens=tokens
            )
        else:
            result = await self.rag_engine.generate_with_retrieval(
                company_id=company_id,
                query=message,
                top_k=3,
                threshold=threshold,
                temperature=temp,
                max_tokens=tokens
            )
        
        return result
