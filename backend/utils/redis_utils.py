"""Redis utilities for caching and rate limiting."""

import logging
import os
import pickle
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast

import redis
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger("app.redis_utils")

# Load environment variables
load_dotenv()

# Redis connection parameters
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_PREFIX = os.getenv("REDIS_PREFIX", "chatbot:")

# Default TTL for cached items (in seconds)
DEFAULT_CACHE_TTL = int(os.getenv("REDIS_CACHE_TTL", "3600"))  # 1 hour

# Type variables for generics
T = TypeVar('T')

# Initialize Redis client
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=False,  # Keep as bytes for pickle compatibility
)


def get_redis_client():
    """Get the Redis client instance."""
    return redis_client


def test_redis_connection() -> bool:
    """
    Test the Redis connection.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        redis_client.ping()
        logger.info("Redis connection successful")
        return True
    except redis.ConnectionError as e:
        logger.error(f"Redis connection error: {str(e)}")
        return False


def redis_cache(ttl: int = DEFAULT_CACHE_TTL, prefix: str = None):
    """
    Decorator for caching function results in Redis.
    
    Args:
        ttl: Time-to-live for cached items in seconds
        prefix: Optional key prefix to use instead of the default
    
    Returns:
        Callable: Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key_parts = [prefix or REDIS_PREFIX, func.__name__]
            
            # Add args and kwargs to key
            if args:
                key_parts.extend([str(arg) for arg in args])
            if kwargs:
                for k, v in sorted(kwargs.items()):
                    key_parts.append(f"{k}:{v}")
            
            cache_key = ":".join(key_parts)
            
            try:
                # Try to get cached result
                cached_result = redis_client.get(cache_key)
                if cached_result:
                    result = pickle.loads(cached_result)
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return result
                
                # No cache hit, execute function
                logger.debug(f"Cache miss for key: {cache_key}")
                result = func(*args, **kwargs)
                
                # Cache the result
                serialized_result = pickle.dumps(result)
                redis_client.setex(cache_key, ttl, serialized_result)
                
                return result
            
            except Exception as e:
                # On error, fall back to the original function
                logger.warning(f"Redis caching error: {str(e)}. Falling back to uncached execution.")
                return func(*args, **kwargs)
                
        return wrapper
    return decorator


def clear_cache(prefix: str = None):
    """
    Clear all cached items with the given prefix.
    
    Args:
        prefix: Optional prefix to clear (defaults to REDIS_PREFIX)
    
    Returns:
        int: Number of keys cleared
    """
    try:
        pattern = f"{prefix or REDIS_PREFIX}:*"
        keys = redis_client.keys(pattern)
        
        if keys:
            count = redis_client.delete(*keys)
            logger.info(f"Cleared {count} keys with pattern {pattern}")
            return count
        else:
            logger.info(f"No keys found matching pattern {pattern}")
            return 0
    
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return 0


class RateLimiter:
    """Rate limiter using Redis."""
    
    def __init__(self, key_prefix: str, limit: int, period: int):
        """
        Initialize the rate limiter.
        
        Args:
            key_prefix: Prefix for rate limiter keys
            limit: Maximum number of requests in the period
            period: Time period in seconds
        """
        self.key_prefix = key_prefix
        self.limit = limit
        self.period = period
    
    def is_allowed(self, client_id: str) -> bool:
        """
        Check if a request is allowed under the rate limit.
        
        Args:
            client_id: Identifier for the client
            
        Returns:
            bool: True if request is allowed, False otherwise
        """
        key = f"{REDIS_PREFIX}:ratelimit:{self.key_prefix}:{client_id}"
        
        try:
            current = redis_client.get(key)
            
            if current is None:
                # First request in period
                redis_client.setex(key, self.period, 1)
                return True
            
            # Convert bytes to int
            current_count = int(current) if current else 0
            
            if current_count < self.limit:
                # Increment counter
                redis_client.incr(key)
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Rate limiter error: {str(e)}")
            # If Redis fails, default to allowing the request
            return True
    
    def get_remaining(self, client_id: str) -> int:
        """
        Get remaining requests allowed in the current period.
        
        Args:
            client_id: Identifier for the client
            
        Returns:
            int: Number of remaining requests allowed
        """
        key = f"{REDIS_PREFIX}:ratelimit:{self.key_prefix}:{client_id}"
        
        try:
            current = redis_client.get(key)
            current_count = int(current) if current else 0
            return max(0, self.limit - current_count)
        
        except Exception as e:
            logger.error(f"Rate limiter error: {str(e)}")
            # If Redis fails, return default value
            return self.limit


# Create rate limiters for different operations
llm_rate_limiter = RateLimiter("llm", limit=50, period=3600)  # 50 LLM requests per hour
embedding_rate_limiter = RateLimiter("embedding", limit=100, period=3600)  # 100 embedding requests per hour