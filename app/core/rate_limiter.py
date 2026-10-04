import time
from typing import Optional
from fastapi import HTTPException, Request, status
from app.db.redis import redis_client



class RateLimiter:
    """Redis-backed fixed/sliding window rate limiter dependency."""

    def __init__(self, times: int = 10, seconds: int = 60):
        self.times = times
        self.seconds = seconds

    async def __call__(self, request: Request) -> None:
        # Determine client identifier (IP address or authenticated user ID if available)
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        
        # Unique Redis key per IP + Endpoint
        redis_key = f"rate_limit:{client_ip}:{path}"

        # Get current hit count
        current_requests = await redis_client.get(redis_key)

        if current_requests and int(current_requests) >= self.times:
            ttl = await redis_client.ttl(redis_key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Try again in {ttl if ttl > 0 else self.seconds} seconds.",
                    "retry_after_seconds": ttl if ttl > 0 else self.seconds,
                },
                headers={"Retry-After": str(ttl if ttl > 0 else self.seconds)},
            )

        # Pipeline increment and expiration for atomic execution
        async with redis_client.pipeline(transaction=True) as pipe:
            pipe.incr(redis_key)
            if not current_requests:
                pipe.expire(redis_key, self.seconds)
            await pipe.execute()