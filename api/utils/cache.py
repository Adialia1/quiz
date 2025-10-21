"""
Redis Caching Utility

Provides high-performance caching layer for API responses
"""
import json
import hashlib
from typing import Optional, Any, Callable
from functools import wraps
import redis.asyncio as redis
import os
from datetime import timedelta

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "true").lower() == "true"

# Redis client instance
_redis_client: Optional[redis.Redis] = None


async def get_redis() -> Optional[redis.Redis]:
    """
    Get Redis client instance (singleton)

    Returns None if Redis is disabled or unavailable
    """
    global _redis_client

    if not REDIS_ENABLED:
        return None

    if _redis_client is None:
        try:
            _redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_keepalive=True,
                health_check_interval=30
            )
            # Test connection
            await _redis_client.ping()
            print(f"✅ Redis connected: {REDIS_HOST}:{REDIS_PORT}")
        except Exception as e:
            print(f"⚠️  Redis connection failed: {e}")
            print(f"⚠️  Continuing without cache...")
            _redis_client = None

    return _redis_client


async def close_redis():
    """Close Redis connection"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate cache key from prefix and arguments

    Args:
        prefix: Cache key prefix (e.g., "user", "topics")
        *args: Positional arguments to include in key
        **kwargs: Keyword arguments to include in key

    Returns:
        Cache key string
    """
    # Create deterministic string from args
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))

    if key_parts:
        # Hash for long keys
        content = ":".join(key_parts)
        content_hash = hashlib.md5(content.encode()).hexdigest()[:12]
        return f"{prefix}:{content_hash}"

    return prefix


async def get_cached(key: str) -> Optional[Any]:
    """
    Get value from cache

    Args:
        key: Cache key

    Returns:
        Cached value (deserialized from JSON) or None
    """
    client = await get_redis()
    if not client:
        return None

    try:
        value = await client.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        print(f"⚠️  Cache read error: {e}")

    return None


async def set_cached(key: str, value: Any, ttl_seconds: int = 300) -> bool:
    """
    Set value in cache

    Args:
        key: Cache key
        value: Value to cache (will be serialized to JSON)
        ttl_seconds: Time to live in seconds (default: 5 minutes)

    Returns:
        True if successful, False otherwise
    """
    client = await get_redis()
    if not client:
        return False

    try:
        serialized = json.dumps(value, ensure_ascii=False, default=str)
        await client.setex(key, ttl_seconds, serialized)
        return True
    except Exception as e:
        print(f"⚠️  Cache write error: {e}")
        return False


async def delete_cached(key: str) -> bool:
    """
    Delete value from cache

    Args:
        key: Cache key

    Returns:
        True if successful, False otherwise
    """
    client = await get_redis()
    if not client:
        return False

    try:
        await client.delete(key)
        return True
    except Exception as e:
        print(f"⚠️  Cache delete error: {e}")
        return False


async def delete_pattern(pattern: str) -> int:
    """
    Delete all keys matching pattern

    Args:
        pattern: Pattern to match (e.g., "user:*")

    Returns:
        Number of keys deleted
    """
    client = await get_redis()
    if not client:
        return 0

    try:
        keys = []
        async for key in client.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            return await client.delete(*keys)
        return 0
    except Exception as e:
        print(f"⚠️  Cache pattern delete error: {e}")
        return 0


def cache_response(
    prefix: str,
    ttl_seconds: int = 300,
    key_builder: Optional[Callable] = None
):
    """
    Decorator to cache endpoint responses

    Args:
        prefix: Cache key prefix
        ttl_seconds: Time to live in seconds
        key_builder: Optional function to build cache key from request args

    Example:
        @cache_response("topics", ttl_seconds=3600)
        async def get_topics():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Use clerk_user_id if available in kwargs
                user_id = kwargs.get("clerk_user_id", "")
                cache_key = generate_cache_key(prefix, user_id, *args)

            # Try to get from cache
            cached_value = await get_cached(cache_key)
            if cached_value is not None:
                print(f"✅ Cache HIT: {cache_key}")
                return cached_value

            # Cache miss - call function
            print(f"❌ Cache MISS: {cache_key}")
            result = await func(*args, **kwargs)

            # Cache result
            await set_cached(cache_key, result, ttl_seconds)

            return result

        return wrapper
    return decorator


# Cache TTL constants (in seconds)
class CacheTTL:
    """Standard cache TTL values"""
    VERY_SHORT = 60          # 1 minute - frequently changing data
    SHORT = 300              # 5 minutes - user stats, progress
    MEDIUM = 900             # 15 minutes - user profiles
    LONG = 3600              # 1 hour - topics, concept counts
    VERY_LONG = 86400        # 24 hours - rarely changing data
    WEEK = 604800            # 7 days - embeddings, static content
