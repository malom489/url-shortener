

from fastapi import APIRouter, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select, update

from app.core.exceptions import LinkNotFoundError
from app.db.redis import redis_client
from app.db.session import async_session
from app.models.link import Link

router = APIRouter()

CACHE_TTL = 3600  # 1 hour


@router.get("/{short_code}")
async def redirect_to_url(short_code: str):
    """Redirect a short code to its original URL. Public endpoint."""

    # 1. Try Redis first (fast path)
    cache_key = f"link:{short_code}"
    cached_url = await redis_client.get(cache_key)

    if cached_url:
        await _increment_click(short_code)
        return RedirectResponse(
            url=cached_url,
            status_code=status.HTTP_301_MOVED_PERMANENTLY,
        )

    # 2. Cache miss — query PostgreSQL
    async with async_session() as db:
        result = await db.execute(select(Link).where(Link.short_code == short_code))
        link = result.scalar_one_or_none()

        if not link:
            raise LinkNotFoundError(
                message=f"Short code '{short_code}' not found.",
                details={"short_code": short_code},
            )

        # 3. Store in Redis for next time
        await redis_client.setex(cache_key, CACHE_TTL, link.original_url)

        # 4. Increment click counter
        await db.execute(
            update(Link)
            .where(Link.id == link.id)
            .values(click_count=Link.click_count + 1)
        )
        await db.commit()

        return RedirectResponse(
            url=link.original_url,
            status_code=status.HTTP_301_MOVED_PERMANENTLY,
        )


async def _increment_click(short_code: str):
    """Increment click count without blocking the redirect."""
    async with async_session() as db:
        await db.execute(
            update(Link)
            .where(Link.short_code == short_code)
            .values(click_count=Link.click_count + 1)
        )
        await db.commit()