import redis
import json
import os

# Connect to Redis using the URL from your .env
_redis_client = None

def get_redis():
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _redis_client = redis.from_url(redis_url, decode_responses=True)
    return _redis_client


def cache_get(key: str):
    """Get a value from cache. Returns None if not found."""
    try:
        r = get_redis()
        value = r.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception:
        # If Redis is down, fail silently — the API still works without cache
        return None


def cache_set(key: str, value, ttl_seconds: int = 3600):
    """Save a value to cache with an expiry time (default: 1 hour)."""
    try:
        r = get_redis()
        r.setex(key, ttl_seconds, json.dumps(value))
    except Exception:
        # If Redis is down, fail silently
        pass


def cache_delete(key: str):
    """Delete a specific key from cache."""
    try:
        r = get_redis()
        r.delete(key)
    except Exception:
        pass


def cache_delete_pattern(pattern: str):
    """Delete all keys matching a pattern, e.g. 'recommendations:*'"""
    try:
        r = get_redis()
        keys = r.keys(pattern)
        if keys:
            r.delete(*keys)
    except Exception:
        pass