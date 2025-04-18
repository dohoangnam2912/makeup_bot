"""
Redis integration with LangChain utilities.
"""

import logging
import pickle
from typing import Dict, List, Optional, Any

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseLanguageModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.retrievers import BaseRetriever

from .redis_utils import redis_cache, redis_client, llm_rate_limiter, embedding_rate_limiter

# Configure logging
logger = logging.getLogger("app.langchain_redis")


class RedisEmbeddingsWrapper(Embeddings):
    """
    Wrapper for embedding models with Redis caching.
    """
    
    def __init__(self, base_embeddings: Embeddings, cache_ttl: int = 86400):
        """
        Initialize with base embeddings model.
        
        Args:
            base_embeddings: Base embeddings model to wrap
            cache_ttl: Time-to-live for cached embeddings (default: 1 day)
        """
        self.base_embeddings = base_embeddings
        self.cache_ttl = cache_ttl
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed documents with caching.
        
        Args:
            texts: List of documents to embed
            
        Returns:
            List[List[float]]: List of embeddings
        """
        # Create a cache key for each text
        results = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            cache_key = f"chatbot:embed_doc:{hash(text)}"
            cached_result = redis_client.get(cache_key)
            
            if cached_result:
                # Cache hit
                results.append(pickle.loads(cached_result))
            else:
                # Cache miss
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Check rate limit for uncached texts
        if uncached_texts and not embedding_rate_limiter.is_allowed("system"):
            logger.warning("Rate limit exceeded for embedding documents")
            raise Exception("Rate limit exceeded for embedding operations")
            
        # Get embeddings for uncached texts
        if uncached_texts:
            uncached_embeddings = self.base_embeddings.embed_documents(uncached_texts)
            
            # Fill in results and cache them
            for i, embedding in zip(uncached_indices, uncached_embeddings):
                cache_key = f"chatbot:embed_doc:{hash(texts[i])}"
                redis_client.setex(cache_key, self.cache_ttl, pickle.dumps(embedding))
                results.insert(i, embedding)
        
        return results
    
    def embed_query(self, text: str) -> List[float]:
        """
        Embed query with caching.
        
        Args:
            text: Query text to embed
            
        Returns:
            List[float]: Query embedding
        """
        cache_key = f"chatbot:embed_query:{hash(text)}"
        cached_result = redis_client.get(cache_key)
        
        if cached_result:
            # Cache hit
            return pickle.loads(cached_result)
        
        # Check rate limit
        if not embedding_rate_limiter.is_allowed("system"):
            logger.warning("Rate limit exceeded for embedding query")
            raise Exception("Rate limit exceeded for embedding operations")
            
        # Cache miss
        embedding = self.base_embeddings.embed_query(text)
        redis_client.setex(cache_key, self.cache_ttl, pickle.dumps(embedding))
        
        return embedding


class RedisLLMWrapper:
    """Wrapper for LLMs with Redis caching and rate limiting."""
    
    def __init__(self, base_llm: BaseLanguageModel, cache_ttl: int = 3600):
        """
        Initialize with base LLM.
        
        Args:
            base_llm: Base language model to wrap
            cache_ttl: Time-to-live for cached responses (default: 1 hour)
        """
        self.base_llm = base_llm
        self.cache_ttl = cache_ttl
    
    @redis_cache(ttl=3600, prefix="chatbot:llm")
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text with caching and rate limiting.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters
            
        Returns:
            str: Generated text
        """
        # Check rate limit
        if not llm_rate_limiter.is_allowed("system"):
            logger.warning("Rate limit exceeded for LLM generation")
            raise Exception("Rate limit exceeded for LLM operations")
        
        # Generate response
        return self.base_llm.predict(prompt, **kwargs)


def get_cached_retriever(retriever: BaseRetriever, cache_ttl: int = 3600) -> BaseRetriever:
    """
    Wrap a retriever with Redis caching.
    
    Args:
        retriever: Base retriever to wrap
        cache_ttl: Time-to-live for cached retrievals
        
    Returns:
        BaseRetriever: Wrapped retriever with caching
    """
    original_get_relevant_documents = retriever._get_relevant_documents
    
    @redis_cache(ttl=cache_ttl, prefix="chatbot:retriever")
    def cached_get_relevant_documents(query: str) -> List[Document]:
        return original_get_relevant_documents(query)
    
    retriever._get_relevant_documents = cached_get_relevant_documents
    
    return retriever


# Function to initialize Redis-cached components
def get_redis_cached_embeddings(base_embeddings: Embeddings) -> RedisEmbeddingsWrapper:
    """Get Redis-cached embeddings."""
    return RedisEmbeddingsWrapper(base_embeddings)


def get_redis_cached_llm(base_llm: BaseLanguageModel) -> RedisLLMWrapper:
    """Get Redis-cached LLM."""
    return RedisLLMWrapper(base_llm)