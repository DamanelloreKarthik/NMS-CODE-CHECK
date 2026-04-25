
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PATCreate(BaseModel):
    name: str
    description: Optional[str] = None
    user_id: UUID
    validity_days: int = Field(gt=0, le=365) 

    
class PATOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    user_name: str    
    token: str
    created_by: str    
    created_at: datetime 
    expires_at: datetime 
    is_active: bool

    class Config:
        from_attributes = True

class PATPaginationResponse(BaseModel):
    items: List[PATOut]
    total: int
    page: int
    page_size: int