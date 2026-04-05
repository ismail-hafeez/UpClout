from pydantic import BaseModel, EmailStr
from typing import Optional


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    displayName: Optional[str] = ""
    userType: Optional[str] = "Influencer"


class LoginRequest(BaseModel):
    username: str
    password: str


class ProfileUpdateRequest(BaseModel):
    displayName: Optional[str] = None
    avatarUrl: Optional[str] = None
