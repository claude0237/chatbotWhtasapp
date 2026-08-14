"""RAG Engine for Retrieval Augmented Generation"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.vector_store import VectorStoreService
from app.ml.embeddings import get_embedding_provider, EmbeddingService
from app.ml.llm import LLMProvider


STRICT_CONTEXT_PROMPT = (
    "Tu es l'assistant officiel de l'entreprise. Ta seule source de vérité est la base de "
    "connaissances fournie ci-dessous.\n\n"
    "Règles:\n"
    "1. Réponds en te basant sur les informations de la base de connaissances. Tu peux "
    "reformuler, expliquer, structurer et développer ces informations pour donner une réponse "
    "claire, complète et professionnelle.\n"
    "2. Tu peux utiliser tes capacités de langage pour rendre la réponse naturelle et pédagogique, "
    "mais tous les FAITS (services, produits, prix, horaires, contacts, procédures) doivent "
    "provenir exclusivement de la base de connaissances.\n"
    "3. N'invente jamais d'information qui ne figure pas dans la base de connaissances.\n"
    "4. Si le client demande quelque chose que l'entreprise ne propose pas (produit, service ou "
    "sujet absent de la base de connaissances), réponds poliment que ce n'est pas proposé, puis "
    "oriente-le vers les produits et services décrits dans la base de connaissances. Termine par "
    "une question pour l'aider à avancer (ex: « Souhaitez-vous en savoir plus sur ... ? »).\n"
    "5. Suis le fil de la conversation et tiens compte des échanges précédents pour ne pas "
    "répéter ce qui a déjà été dit.\n\n"
    "Base de connaissances:\n\n{context}"
)


class RAGEngine:
    """RAG Engine for retrieval augmented generation"""
    
    def __init__(self, db: AsyncSession, llm_provider: Optional[LLMProvider] = None):
        self.db = db
        self.vector_store = VectorStoreService(db)
        
        # Initialize embedding service
        embedding_provider = get_embedding_provider(provider_type="local")
        self.embedding_service = EmbeddingService(embedding_provider)
        
        # Initialize LLM provider
        self.llm_provider = llm_provider
    
    def _calculate_response_quality(self, response: str, context: Optional[str]) -> float:
        """Calculate response quality based on overlap with context
        
        Returns a score between 0 and 1:
        - 1.0: Response heavily based on context
        - 0.5: Response partially based on context
        - 0.0: No overlap with context
        """
        if not context:
            return 0.5  # Neutral score if no context
        
        # Normalize text
        response_lower = response.lower()
        context_lower = context.lower()
        
        # Tokenize into words (remove punctuation)
        import re
        response_words = set(re.findall(r'\b\w+\b', response_lower))
        context_words = set(re.findall(r'\b\w+\b', context_lower))
        
        if not response_words:
            return 0.0
        
        # Calculate overlap ratio
        overlap = len(response_words & context_words)
        overlap_ratio = overlap / len(response_words)
        
        # Bonus for longer responses with good overlap
        length_bonus = min(len(response_words) / 50, 0.2)  # Max 0.2 bonus
        
        # Combine overlap with length bonus
        quality_score = min(overlap_ratio + length_bonus, 1.0)
        
        return quality_score
    
    async def retrieve(
        self,
        company_id: UUID,
        query: str,
        top_k: int = 5,
        threshold: float = 0.6
    ) -> List[tuple[str, float]]:
        """Retrieve relevant chunks from unified vector store (documents + knowledge base).
        
        threshold is the MINIMUM similarity (0-1); converted to max cosine distance for pgvector.
        """
        try:
            query_embedding = await self.embedding_service.embed_text(query)
            similar_chunks = await self.vector_store.search_similar(
                company_id=company_id,
                query_embedding=query_embedding,
                limit=top_k,
                threshold=1.0 - threshold
            )
            if similar_chunks:
                return [(chunk.content, similarity) for chunk, similarity in similar_chunks]
        except Exception as e:
            import logging
            logger = logging.getLogger("app.ml.rag")
            logger.error(f"Vector search failed: {str(e)}")
        
        return []
    
    async def generate(
        self,
        query: str,
        context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Generate response using LLM"""
        if not self.llm_provider:
            raise RuntimeError("LLM provider not configured")
        
        return await self.llm_provider.generate_response(
            prompt=query,
            context=context,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    async def generate_with_retrieval(
        self,
        company_id: UUID,
        query: str,
        top_k: int = 3,
        threshold: float = 0.6,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """Generate response with RAG (retrieve context then generate)"""
        # Retrieve relevant chunks
        retrieved_chunks = await self.retrieve(
            company_id=company_id,
            query=query,
            top_k=top_k,
            threshold=threshold
        )
        
        if not retrieved_chunks:
            # Best-effort retrieval: give the model the company offering so it can
            # politely redirect the client instead of staying silent.
            retrieved_chunks = await self.retrieve(
                company_id=company_id,
                query=query,
                top_k=top_k,
                threshold=0.0
            )
        
        if not retrieved_chunks:
            # Knowledge base is completely empty: fall back to the configured unknown message.
            return {
                "response": "",
                "context": None,
                "sources": [],
                "confidence": 0.0,
                "retrieval_confidence": 0.0,
                "response_quality": 0.0
            }
        
        # Build context from retrieved chunks
        context_parts = []
        sources = []
        for content, similarity in retrieved_chunks:
            context_parts.append(content)
            sources.append({
                "content": content[:200] + "..." if len(content) > 200 else content,
                "similarity": similarity
            })
        
        context = "\n\n".join(context_parts)
        
        # Generate response with strict context-only prompt
        response = await self.generate(
            query=query,
            context=STRICT_CONTEXT_PROMPT.format(context=context),
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Calculate retrieval confidence (average similarity)
        retrieval_confidence = sum(sim for _, sim in retrieved_chunks) / len(retrieved_chunks)
        
        # Calculate response quality (overlap with context)
        response_quality = self._calculate_response_quality(response, context)
        
        # Combine both: 60% retrieval, 40% response quality
        combined_confidence = (0.6 * retrieval_confidence) + (0.4 * response_quality)
        
        return {
            "response": response,
            "context": context,
            "sources": sources,
            "confidence": combined_confidence,
            "retrieval_confidence": retrieval_confidence,
            "response_quality": response_quality
        }
    
    async def generate_with_history(
        self,
        company_id: UUID,
        query: str,
        conversation_history: List[Dict[str, str]],
        top_k: int = 3,
        threshold: float = 0.6,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """Generate response with RAG and conversation history"""
        # Retrieve relevant chunks
        retrieved_chunks = await self.retrieve(
            company_id=company_id,
            query=query,
            top_k=top_k,
            threshold=threshold
        )
        
        if not retrieved_chunks:
            # Best-effort retrieval: give the model the company offering so it can
            # politely redirect the client instead of staying silent.
            retrieved_chunks = await self.retrieve(
                company_id=company_id,
                query=query,
                top_k=top_k,
                threshold=0.0
            )
        
        if not retrieved_chunks:
            # Knowledge base is completely empty: fall back to the configured unknown message.
            return {
                "response": "",
                "context": None,
                "sources": [],
                "confidence": 0.0,
                "retrieval_confidence": 0.0,
                "response_quality": 0.0
            }
        
        # Build messages for LLM with strict context-grounded prompt
        messages = []
        context_parts = [content for content, _ in retrieved_chunks]
        context = "\n\n".join(context_parts)
        messages.append({
            "role": "system",
            "content": STRICT_CONTEXT_PROMPT.format(context=context)
        })
        
        # Add conversation history
        messages.extend(conversation_history)
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        # Generate response
        if not self.llm_provider:
            raise RuntimeError("LLM provider not configured")
        
        response = await self.llm_provider.generate_response_with_history(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Calculate retrieval confidence (average similarity)
        retrieval_confidence = sum(sim for _, sim in retrieved_chunks) / len(retrieved_chunks)
        
        # Calculate response quality (overlap with context)
        response_quality = self._calculate_response_quality(response, context)
        
        # Combine both: 60% retrieval, 40% response quality
        combined_confidence = (0.6 * retrieval_confidence) + (0.4 * response_quality)
        
        sources = [
            {
                "content": content[:200] + "..." if len(content) > 200 else content,
                "similarity": similarity
            }
            for content, similarity in retrieved_chunks
        ]
        
        return {
            "response": response,
            "context": context,
            "sources": sources,
            "confidence": combined_confidence,
            "retrieval_confidence": retrieval_confidence,
            "response_quality": response_quality
        }
