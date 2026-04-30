from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    is_active: bool
    is_admin: bool

    model_config = {"from_attributes": True}


# ===== 管理员用户管理 =====

class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str | None = Field(None, description="留空则自动生成")
    is_admin: bool = False


class UpdateUserRequest(BaseModel):
    is_active: bool | None = None
    is_admin: bool | None = None


class UserAdminOut(BaseModel):
    id: int
    username: str
    is_active: bool
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CreateUserResponse(BaseModel):
    user: UserAdminOut
    generated_password: str | None = None
