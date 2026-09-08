
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.users import User
from app.schemas.user import UserCreate, UserResponse
from app.services.auth import hash_password
from app.schemas.user import UserLogin, Token
from app.services.auth import verify_password, generate_jwt_token

router=APIRouter()

@router.post("/register",response_model=UserResponse,status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # ChecK USER EXISTENCE
    stmt = select(User).where(User.email == user.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists")

    # Hash the password
    hashed_password = hash_password(user.password)

    # Create new user
    new_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        tenant_id=user.tenant_id
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user
@router.post("/Login",response_model=Token)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    access_token = generate_jwt_token(user_id=user.id, tenant_id=user.tenant_id)
    return Token(access_token=access_token)