

import redis.asyncio as redis

from app.core.config import settings

# Create connection pool
redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


async def get_redis():
    """Dependency for Redis client."""
    return redis_client
