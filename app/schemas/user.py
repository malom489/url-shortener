from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr
class UserCreate(BaseModel):
    email:EmailStr
    full_name:str
    password:str
    tenant_id:str
class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    tenant_id: str
    is_active: bool
    created_at: datetime  
    model_config = ConfigDict(from_attributes=True)
    
class UserLogin(BaseModel):
    email:EmailStr
    password:str 
    
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None
    tenant_id: Optional[str] = None