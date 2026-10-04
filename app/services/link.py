from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.redis import redis_client
from app.models.link import Link

CACHE_TTL = 3600  # 1 hour


class LinkService:

    @staticmethod
    async def get_url_by_code(short_code: str, db: AsyncSession) -> Optional[str]:
        """Fetch URL from Redis cache or Postgres database."""
        cache_key = f"link:{short_code}"

        # 1. Redis Cache Hit
        cached_url = await redis_client.get(cache_key)
        if cached_url:
            return cached_url if isinstance(cached_url, str) else cached_url.decode("utf-8")

        # 2. Redis Cache Miss -> DB Query
        result = await db.execute(
            select(Link).where(Link.short_code == short_code)
        )
        link = result.scalar_one_or_none()

        if not link:
            return None

        # 3. Populate Redis Cache
        await redis_client.setex(cache_key, CACHE_TTL, link.original_url)
        return link.original_url

    @staticmethod
    async def increment_click_count(short_code: str, db: AsyncSession) -> None:
        """Asynchronously update link click metrics in Postgres."""
        await db.execute(
            update(Link)
            .where(Link.short_code == short_code)
            .values(click_count=Link.click_count + 1)
        )
        await db.commit()
    
