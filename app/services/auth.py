from passlib.context import CryptContext
import jwt
from fastapi import Depends,HTTPException,status
from fastapi.security import OAuth2PasswordBearer

from datetime import datetime,timedelta
from app.core.config  import settings
from  sqlalchemy import select 
from sqlalchemy.ext.asyncio import AsyncSession


from app.db.session import get_db
from app.models.users import User
from app.core.config import settings

pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")
oauth2_scheme=OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def hash_password(password:str)->str:
    return pwd_context.hash(password)
def verify_password(plain_password:str,hashed_password:str)->bool:
    return pwd_context.verify(plain_password,hashed_password)

def generate_jwt_token(user_id:int,tenant_id:str)->str:
    expire=datetime.utcnow()+timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload={
        "sub":str(user_id),
        "tenant_id":str(tenant_id),
        "exp":expire,
    }
    return jwt.encode(payload,settings.SECRET_KEY,algorithm=settings.ALGORITHM)
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError as e:
        raise credentials_exception from e

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception
    return user