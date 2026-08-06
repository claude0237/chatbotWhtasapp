"""ML Engine for orchestrating RAG and LLM"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.rag import RAGEngine
from app.ml.llm import get_llm_provider, LLMProvider
from app.bot.models import BotConfiguration, MLProvider, FallbackStrategy
from app.bot.repositories import BotConfigurationRepository


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
            self.llm_provider = get_llm_provider(provider_type)
        else:
            self.llm_provider = get_llm_provider("openai")  # Default
        
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
    
    async def process_with_fallback(
        self,
        company_id: UUID,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        native_response: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process message with fallback strategy"""
        config = await self.config_repository.get_active_configuration(company_id)
        
        if not config or not config.ml_enabled:
            return {
                "response": native_response or "ML not enabled",
                "source": "native",
                "confidence": 0.0
            }
        
        fallback_strategy = config.fallback_strategy if config.fallback_strategy else FallbackStrategy.ML_TO_NATIVE
        
        # ML_TO_NATIVE: Try ML first, fallback to native if low confidence
        if fallback_strategy == FallbackStrategy.ML_TO_NATIVE:
            try:
                ml_result = await self.process_message(company_id, message, conversation_history)
                
                # Check confidence threshold
                confidence_threshold = float(config.confidence_threshold) if config.confidence_threshold else 0.5
                if ml_result["confidence"] >= confidence_threshold:
                    return {
                        "response": ml_result["response"],
                        "source": "ml",
                        "confidence": ml_result["confidence"],
                        "context": ml_result.get("context"),
                        "sources": ml_result.get("sources", [])
                    }
                else:
                    # Fallback to native
                    return {
                        "response": native_response or "I'm not confident about that answer.",
                        "source": "native_fallback",
                        "confidence": ml_result["confidence"]
                    }
            except Exception as e:
                # Fallback to native on error
                return {
                    "response": native_response or "ML processing failed.",
                    "source": "native_fallback",
                    "error": str(e)
                }
        
        # NATIVE_TO_ML: Try native first, use ML if no good response
        elif fallback_strategy == FallbackStrategy.NATIVE_TO_ML:
            if native_response and native_response not in ["I'm not sure how to help with that.", "Unknown"]:
                return {
                    "response": native_response,
                    "source": "native",
                    "confidence": 1.0
                }
            else:
                # Fallback to ML
                try:
                    ml_result = await self.process_message(company_id, message, conversation_history)
                    return {
                        "response": ml_result["response"],
                        "source": "ml_fallback",
                        "confidence": ml_result["confidence"],
                        "context": ml_result.get("context"),
                        "sources": ml_result.get("sources", [])
                    }
                except Exception as e:
                    return {
                        "response": "Both native and ML failed.",
                        "source": "error",
                        "error": str(e)
                    }
        
        # PARALLEL: Run both and choose best
        elif fallback_strategy == FallbackStrategy.PARALLEL:
            try:
                ml_result = await self.process_message(company_id, message, conversation_history)
                
                # Compare confidence and choose best
                if ml_result["confidence"] >= 0.7:
                    return {
                        "response": ml_result["response"],
                        "source": "ml",
                        "confidence": ml_result["confidence"],
                        "context": ml_result.get("context"),
                        "sources": ml_result.get("sources", [])
                    }
                else:
                    return {
                        "response": native_response or ml_result["response"],
                        "source": "hybrid",
                        "confidence": ml_result["confidence"]
                    }
            except Exception as e:
                return {
                    "response": native_response or "ML processing failed.",
                    "source": "native_fallback",
                    "error": str(e)
                }
        
        return {
            "response": native_response or "No response available.",
            "source": "none",
            "confidence": 0.0
        }
