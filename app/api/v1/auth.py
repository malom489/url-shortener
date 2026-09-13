from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.db.session import get_db
from app.models.users import User
from app.schemas.user import UserCreate, UserResponse, UserLogin, Token
from app.services.auth import hash_password, verify_password, generate_jwt_token

router = APIRouter(prefix="/auth", tags=["auth"])


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    existing_user = await get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    hashed_password = hash_password(user.password)

    new_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        tenant_id=user.tenant_id,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_email(db, form_data.username)

    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
    )

    if not user or not verify_password(
        form_data.password,
        user.hashed_password,
    ):
        raise invalid_credentials

    if not user.is_active:
        raise invalid_credentials

    access_token = generate_jwt_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
    )

    return Token(access_token=access_token)

