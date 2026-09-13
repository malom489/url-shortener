from fastapi import APIRouter, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select, update

from app.db.session import SessionLocal
from app.models.link import Link
from fastapi import APIRouter, HTTPException, status

router = APIRouter()




@router.get("/{short_code}")
async def redirect_to_url(short_code: str):

    async with SessionLocal() as db:
        result = await db.execute(
            select(Link).where(Link.short_code == short_code)
        )

        link = result.scalar_one_or_none()
        if not link:
           raise HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail=f"Short code '{short_code}' not found.",
        )
        
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
