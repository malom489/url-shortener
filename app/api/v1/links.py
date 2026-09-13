
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from app.db.session import get_db
from app.models.link import Link
from app.models.users import User
from app.schemas.link import LinkCreate, LinkResponse
from app.services.auth import get_current_user
from app.services.short_code import generate_short_code

router = APIRouter()


@router.post("/", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def create_link(
    link_in: LinkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a shortened link. Requires authentication."""
    if link_in.custom_code:
        result = await db.execute(select(Link).where(Link.short_code == link_in.custom_code))
        if result.scalars().first():
            raise ShortCodeCollisionError(
                message="This custom code is already in use.",
                details={"custom_code": link_in.custom_code},
            )
        short_code = link_in.custom_code
    else:
        for _ in range(5):
            short_code = generate_short_code()
            result = await db.execute(select(Link).where(Link.short_code == short_code))
            if not result.scalars().first():
                break
        else:
            raise ShortCodeCollisionError(
                message="Could not generate a unique short code. Try again.",
            )

    link = Link(
        tenant_id=current_user.tenant_id,
        short_code=short_code,
        original_url=link_in.original_url,
        created_by=current_user.id,
    )

    db.add(link)
    await db.flush()
    await db.refresh(link)
    return link


@router.get("/", response_model=list[LinkResponse])
async def list_links(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all links for the current user's tenant."""
    result = await db.execute(
        select(Link)
        .where(Link.tenant_id == current_user.tenant_id)
        .order_by(Link.created_at.desc())
    )
    return result.scalars().all()
