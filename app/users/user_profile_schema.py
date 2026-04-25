
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID


class UserProfileCreate(BaseModel):
    name: str
    description: Optional[str] = None
    scope_by: str
    user_id: UUID
    role_id: UUID
    group_id: Optional[UUID] = None

class UserProfileResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    scope_by: str

    user_id: Optional[UUID] = None 
    user: Optional[str] = None

    role_id: Optional[UUID] = None
    role: Optional[str] = None

    group_id: Optional[UUID] = None
    group: Optional[str] = None

    class Config:
        from_attributes = True


class UserProfilePaginationResponse(BaseModel):
    items: List[UserProfileResponse]
    total: int
    page: int
    page_size: int