"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum
from uuid import UUID


class UserRole(str, Enum):
    """User roles."""

    ADMIN = "admin"
    TECHNICIAN = "technician"
    CLIENT = "client"
    COMPANY = "company"


class UserBase(BaseModel):
    """Shared user attributes across operations."""

    name: str
    email: EmailStr
    role: UserRole = UserRole.CLIENT
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema."""

    password: str


class UserUpdate(BaseModel):
    """User update schema."""

    name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None


class UserResponse(UserBase):
    """User response schema."""

    id: UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    user_id: Optional[UUID] = None
    user_name: Optional[str] = None
    roles: list[str] = Field(default_factory=list)
    hubs: list[dict] = Field(default_factory=list)
    current_hub_id: Optional[UUID] = None
    hub_id: Optional[UUID] = None
    hub_code: Optional[str] = None
    hub_name: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str
    hub_code: Optional[str] = None
