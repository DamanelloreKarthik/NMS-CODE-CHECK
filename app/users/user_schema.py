
from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

class UserCreate(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    username: str
    email: EmailStr
    mobile_number: Optional[str] = None

    password: str
    confirm_password: str

    role_id: Optional[UUID] = None
    group_id: Optional[UUID] = None

    is_active: bool = True

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    username: Optional[str] = None
    email: Optional[EmailStr] = None

    mobile_number: Optional[str] = None

    role_id: Optional[UUID] = None
    group_id: Optional[UUID] = None

    is_active: Optional[bool] = None


# =========================
# RESPONSE USER
# =========================
class UserOut(BaseModel):
    id: UUID
    user_code: Optional[str] = None

    first_name: Optional[str] = None
    last_name: Optional[str] = None

    username: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = None

    role_id: Optional[UUID] = None
    group_id: Optional[UUID] = None

    is_active: bool

    class Config:
        from_attributes = True   