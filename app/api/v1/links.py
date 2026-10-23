from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

# Note: Commented out until you actually build the rate limiter.
# from app.core.rate_limiter import RateLimiter 
from app.core.exceptions import ShortCodeCollisionError, LinkCreationError,LinkNotFoundError
from app.db.session import get_db
from app.models.link import Link
from app.models.user import User
from app.schemas.link import LinkCreate, LinkResponse
from app.services.auth import get_current_user
from app.services.short_code import generate_short_code
from app.db.redis import redis_client

router = APIRouter()

@router.post(
    "/",
    # dependencies=[Depends(RateLimiter(times=10, seconds=60))],
    status_code=status.HTTP_201_CREATED,
)
async def create_link(
    link_in: LinkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a shortened link. Requires authentication."""
    
    # 1. Determine the short code
    if link_in.custom_code:
        # Fast pre-check for a friendly error message
        result = await db.execute(select(Link).where(Link.short_code == link_in.custom_code))
        if result.scalars().first():
            raise ShortCodeCollisionError(
                message="This custom code is already in use.",
                details={"custom_code": link_in.custom_code},
            )
        short_code = link_in.custom_code
    else:
        # Generate a random code with retries
        for _ in range(5):
            short_code = generate_short_code()
            result = await db.execute(select(Link).where(Link.short_code == short_code))
            if not result.scalars().first():
                break
        else:
            raise ShortCodeCollisionError(
                message="Could not generate a unique short code. Try again.",
            )

    # 2. Create the database record
    link = Link(
        tenant_id=current_user.tenant_id,
        short_code=short_code,
        original_url=link_in.original_url,
        created_by=current_user.id,
    )
    db.add(link)

    # 3. Commit and handle the Race Condition (The 500 Fix)
    try:
        await db.commit()
        await db.refresh(link)  # Get the generated ID and created_at
        
    except IntegrityError:
        # This happens if someone else inserted the SAME short_code 
        # between our pre-check and our commit.
        await db.rollback()
        
        # If it was a custom code, tell the user it's taken.
        if link_in.custom_code:
            raise ShortCodeCollisionError(
                message="This custom code was just taken. Please try another.",
                details={"custom_code": link_in.custom_code},
            )
        
        # If it was a random code, ask the client to retry.
        raise LinkCreationError(
            message="A collision occurred while generating the short code. Please retry."
        )

    # 4. Return the response
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
@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    link_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Link).where(
            Link.id == link_id,
            Link.tenant_id == current_user.tenant_id,
        )
    )
    link = result.scalars().first()

    if not link:
        raise LinkNotFoundError(message="Link not found.")

    short_code = link.short_code

    await db.delete(link)
    await db.commit()

    try:
        await redis_client.delete(f"link:{short_code}")
    except Exception as e:
        logger.error(f"Failed to invalidate cache for {short_code}: {e}")