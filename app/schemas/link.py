from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class LinkCreate(BaseModel):
    original_url:str
    custom_code:Optional[str]=None
    
    
class LinkResponse(BaseModel):
    id:int 
    short_code:str 
    original_url:str 
    click_count:int 
    created_at:datetime  
    
    model_config = ConfigDict(from_attributes=True)