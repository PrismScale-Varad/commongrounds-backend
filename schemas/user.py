from pydantic import BaseModel, EmailStr
from typing import List, Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    username: str
    interests: List[str]
    profile_pic: Optional[str] = None
    location: Optional[str] = None

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: Optional[str] = None
    profile_pic: Optional[str] = None
    location: Optional[str] = None
    interests: Optional[List[str]] = None

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    profile_pic: Optional[str] = None
    location: Optional[str] = None
    interests: Optional[List[str]] = None

    class Config:
        from_attributes = True

class PasswordReset(BaseModel):
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

    class Config:
        from_attributes = True

class LoginCredentials(BaseModel):
    email: EmailStr
    password: str
