
from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import LinkNotFoundError
from app.db.session import get_db
from app.services.link import LinkService

router = APIRouter()


@router.get("/{short_code}", response_class=RedirectResponse)
async def redirect_to_url(
    short_code: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Redirect a short code to its destination URL."""
    original_url = await LinkService.get_url_by_code(short_code, db)

    if not original_url:
        raise LinkNotFoundError(
            message=f"Short code '{short_code}' not found.",
            details={"short_code": short_code},
        )

    # Schedule click counting in the background so redirect isn't blocked by DB write
    background_tasks.add_task(LinkService.increment_click_count, short_code, db)

    return RedirectResponse(
        url=original_url,
        status_code=status.HTTP_302_FOUND,  # Prevents client-side aggressive browser caching
    )