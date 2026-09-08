from datetime import datetime
from typing import Optional, Optional
from pydantic import BaseModel, BaseModel,EmailStr
class UserCreate(BaseModel):
    email:EmailStr
    full_name:str
    password:str
    tenant_id:int
class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    tenant_id: int
    is_active: bool
    created_at: datetime  
    class config:
               from_attributes =True
    
class UserLogin(BaseModel):
    email:EmailStr
    password:str 
    
class Token(BaseModel):
    access_token:str
    token_type:str="bearer"
    