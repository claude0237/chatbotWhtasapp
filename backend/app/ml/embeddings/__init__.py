"""Embedding Providers and Service"""
from typing import List, Optional
from abc import ABC, abstractmethod
import json
import redis.asyncio as redis
from app.config import settings


class EmbeddingProvider(ABC):
    """Base interface for embedding providers"""
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
    
    @abstractmethod
    async def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider"""
    
    def __init__(self, api_key: str, model: str = "text-embedding-ada-002"):
        self.api_key = api_key
        self.model = model
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API"""
        try:
            import openai
            openai.api_key = self.api_key
            
            response = await openai.Embedding.acreate(
                model=self.model,
                input=text
            )
            return response["data"][0]["embedding"]
        except ImportError:
            raise ImportError("OpenAI library not installed")
        except Exception as e:
            raise RuntimeError(f"OpenAI embedding generation failed: {str(e)}")
    
    async def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using OpenAI API"""
        try:
            import openai
            openai.api_key = self.api_key
            
            response = await openai.Embedding.acreate(
                model=self.model,
                input=texts
            )
            return [item["embedding"] for item in response["data"]]
        except ImportError:
            raise ImportError("OpenAI library not installed")
        except Exception as e:
            raise RuntimeError(f"OpenAI batch embedding generation failed: {str(e)}")


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local embedding provider using sentence-transformers"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
    
    async def _load_model(self):
        """Load the model lazily"""
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self.model_name)
            except ImportError:
                raise ImportError("sentence-transformers library not installed")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using local model"""
        await self._load_model()
        embedding = self.model.encode(text)
        return embedding.tolist()
    
    async def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using local model"""
        await self._load_model()
        embeddings = self.model.encode(texts)
        return [emb.tolist() for emb in embeddings]


class EmbeddingService:
    """Service for managing embeddings with caching"""
    
    def __init__(self, provider: EmbeddingProvider, redis_client: Optional[redis.Redis] = None):
        self.provider = provider
        self.redis_client = redis_client
        self.cache_ttl = 3600  # 1 hour
    
    async def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"embedding:{text_hash}"
    
    async def _get_from_cache(self, cache_key: str) -> Optional[List[float]]:
        """Get embedding from Redis cache"""
        if self.redis_client:
            try:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass
        return None
    
    async def _set_cache(self, cache_key: str, embedding: List[float]):
        """Set embedding in Redis cache"""
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(embedding)
                )
            except Exception:
                pass
    
    async def embed_text(self, text: str, use_cache: bool = True) -> List[float]:
        """Generate embedding for a single text with optional caching"""
        if use_cache:
            cache_key = await self._get_cache_key(text)
            cached_embedding = await self._get_from_cache(cache_key)
            if cached_embedding:
                return cached_embedding
        
        embedding = await self.provider.generate_embedding(text)
        
        if use_cache:
            await self._set_cache(cache_key, embedding)
        
        return embedding
    
    async def batch_embed(self, texts: List[str], use_cache: bool = True) -> List[List[float]]:
        """Generate embeddings for multiple texts with optional caching"""
        embeddings = []
        texts_to_embed = []
        indices_to_embed = []
        
        # Check cache for each text
        for i, text in enumerate(texts):
            if use_cache:
                cache_key = await self._get_cache_key(text)
                cached_embedding = await self._get_from_cache(cache_key)
                if cached_embedding:
                    embeddings.append(cached_embedding)
                else:
                    texts_to_embed.append(text)
                    indices_to_embed.append(i)
            else:
                texts_to_embed.append(text)
                indices_to_embed.append(i)
        
        # Generate embeddings for texts not in cache
        if texts_to_embed:
            new_embeddings = await self.provider.generate_batch_embeddings(texts_to_embed)
            
            # Cache new embeddings and place them in correct positions
            for idx, embedding in zip(indices_to_embed, new_embeddings):
                if use_cache:
                    cache_key = await self._get_cache_key(texts_to_embed[indices_to_embed.index(idx)])
                    await self._set_cache(cache_key, embedding)
                
                # Insert embedding at correct position
                while len(embeddings) <= idx:
                    embeddings.append([])
                embeddings[idx] = embedding
        
        return embeddings
    
    async def embed_document_chunks(self, chunks: List[str], use_cache: bool = True) -> List[List[float]]:
        """Generate embeddings for document chunks"""
        return await self.batch_embed(chunks, use_cache)


# Factory function to get embedding provider
def get_embedding_provider(provider_type: str = "openai") -> EmbeddingProvider:
    """Get embedding provider by type"""
    if provider_type == "openai":
        return OpenAIEmbeddingProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_embedding_model or "text-embedding-ada-002"
        )
    elif provider_type == "local":
        return LocalEmbeddingProvider(
            model_name=settings.local_embedding_model or "all-MiniLM-L6-v2"
        )
    else:
        raise ValueError(f"Unsupported embedding provider: {provider_type}")


async def get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client for caching (async)"""
    if settings.redis_url:
        return redis.from_url(settings.redis_url, decode_responses=True)
    return None
