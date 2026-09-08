from passlib.context import CryptContext
import jwt
from datetime import datetime,timedelta
from app.core.config  import settings
pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")
 
 
def hash_password(password:str)->str:
    return pwd_context.hash(password)
def verify_password(plain_password:str,hashed_password:str)->bool:
    return pwd_context.verify(plain_password,hashed_password)

def generate_jwt_token(user_id:int,tenant_id:int)->str:
    expire=datetime.utcnow()+timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload={
        "sub":str(user_id),
        "tenant_id":str(tenant_id),
        "exp":expire,
    }
    return jwt.encode(payload,settings.SECRET_KEY,algorithm=settings.ALGORITHM)