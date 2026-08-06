"""RAG Engine for Retrieval Augmented Generation"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.vector_store import VectorStoreService
from app.ml.embeddings import get_embedding_provider, EmbeddingService
from app.ml.llm import get_llm_provider, LLMProvider
from app.bot.models import MLProvider as BotMLProvider


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
    
    async def retrieve(
        self,
        company_id: UUID,
        query: str,
        top_k: int = 5,
        threshold: float = 0.5
    ) -> List[tuple[str, float]]:
        """Retrieve relevant chunks from knowledge base"""
        # Try vector search first
        try:
            query_embedding = await self.embedding_service.embed_text(query)
            similar_chunks = await self.vector_store.search_similar(
                company_id=company_id,
                query_embedding=query_embedding,
                limit=top_k,
                threshold=threshold
            )
            if similar_chunks:
                return [(chunk.content, similarity) for chunk, similarity in similar_chunks]
        except Exception as e:
            print(f"Vector search failed: {str(e)}")
        
        # Fallback to text search in knowledge_base table
        from sqlalchemy import select, and_, or_
        from app.knowledge.models import KnowledgeBase
        
        result = await self.db.execute(
            select(KnowledgeBase).where(
                and_(
                    KnowledgeBase.company_id == company_id,
                    KnowledgeBase.is_active == True
                )
            )
        )
        entries = result.scalars().all()
        
        # Simple text matching based on query terms
        query_terms = query.lower().split()
        scored_entries = []
        
        for entry in entries:
            content_lower = entry.content.lower()
            title_lower = entry.title.lower()
            
            # Calculate simple relevance score
            score = 0.0
            for term in query_terms:
                if term in content_lower:
                    score += 0.5
                if term in title_lower:
                    score += 0.3
            
            if score > 0:
                scored_entries.append((entry.content, min(score, 1.0)))
        
        # Sort by score and return top results
        scored_entries.sort(key=lambda x: x[1], reverse=True)
        return scored_entries[:top_k]
    
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
        threshold: float = 0.5,
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
            # No relevant context found, generate without context
            response = await self.generate(
                query=query,
                context=None,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return {
                "response": response,
                "context": None,
                "sources": [],
                "confidence": 0.0
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
        
        # Generate response with context
        response = await self.generate(
            query=query,
            context=f"Use the following context to answer the question:\n\n{context}",
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Calculate average confidence
        avg_confidence = sum(sim for _, sim in retrieved_chunks) / len(retrieved_chunks)
        
        return {
            "response": response,
            "context": context,
            "sources": sources,
            "confidence": avg_confidence
        }
    
    async def generate_with_history(
        self,
        company_id: UUID,
        query: str,
        conversation_history: List[Dict[str, str]],
        top_k: int = 3,
        threshold: float = 0.5,
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
        
        # Build messages for LLM
        messages = []
        
        # Add system prompt with context if available
        if retrieved_chunks:
            context_parts = [content for content, _ in retrieved_chunks]
            context = "\n\n".join(context_parts)
            messages.append({
                "role": "system",
                "content": f"Use the following context to answer the question:\n\n{context}"
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
        
        # Calculate average confidence
        avg_confidence = sum(sim for _, sim in retrieved_chunks) / len(retrieved_chunks) if retrieved_chunks else 0.0
        
        sources = [
            {
                "content": content[:200] + "..." if len(content) > 200 else content,
                "similarity": similarity
            }
            for content, similarity in retrieved_chunks
        ]
        
        return {
            "response": response,
            "context": "\n\n".join([content for content, _ in retrieved_chunks]) if retrieved_chunks else None,
            "sources": sources,
            "confidence": avg_confidence
        }
