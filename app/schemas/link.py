from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class LinkCreate(BaseModel):
    original_url:str
    custom_code:Optional[str]=None
    
    
class LinkResponse(BaseModel):
    id:int 
    short_code:str 
    original_url:str 
    click_count:int 
    created_at:datetime  
    
    class Config:
        from_attributes=True