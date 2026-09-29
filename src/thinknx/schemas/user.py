from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class UserBase(BaseModel):
    email: Optional[str] = Field(default=None, description="User email address")
    clerk_id: Optional[str] = Field(default=None, description="Clerk User ID")
    telegram_id: Optional[str] = Field(default=None, description="Telegram User ID")
    name: Optional[str] = None
    platform: str = "telegram"
    explanation_level: str = "beginner"
    timezone: str = "UTC"


class UserCreate(UserBase):
    password: Optional[str] = None


class UserResponse(UserBase):
    id: str
    interests: List[str] = []
    goals: List[Dict[str, Any]] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdateInterests(BaseModel):
    interests: List[str]
    goals: Optional[List[Dict[str, Any]]] = None
    explanation_level: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
