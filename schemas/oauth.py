from pydantic import BaseModel, EmailStr
from typing import Optional, List

class OAuthSetupProfile(BaseModel):
    """
    Schema for setting up or updating additional profile data for an OAuth user.
    All fields are optional so that users can provide only the fields they want to update.
    """
    username: Optional[str] = None
    profile_pic: Optional[str] = None
    location: Optional[str] = None
    interests: Optional[List[str]] = None

    class Config:
        orm_mode = True

class OAuthUserResponse(BaseModel):
    """
    Minimal response schema for an OAuth user.
    This may be used to return a user's profile information after signup or login.
    """
    id: int
    email: EmailStr
    username: Optional[str] = None
    profile_pic: Optional[str] = None
    location: Optional[str] = None
    interests: Optional[List[str]] = None

    class Config:
        orm_mode = True
