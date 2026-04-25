from pydantic import BaseModel
from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    # full_name: str
    email: EmailStr
    password: str
    role: str
    is_active: bool = True
    first_name:str
    last_name:str
    

class LoginRequest(BaseModel):
    email: str
    password: str
