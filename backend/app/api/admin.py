"""管理员路由：用户管理（仅 admin 可用）。"""
from __future__ import annotations

import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_db
from app.core.security import hash_password
from app.models.user import User
from app.schemas.auth import (
    CreateUserRequest,
    CreateUserResponse,
    UpdateUserRequest,
    UserAdminOut,
)
from app.schemas.common import MessageResponse

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_admin)],
)


def _gen_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))


@router.get("/users", response_model=list[UserAdminOut])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.id))
    return result.scalars().all()


@router.post("/users", response_model=CreateUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(payload: CreateUserRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == payload.username))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="用户名已存在")

    generated: str | None = None
    plain_pw = payload.password
    if not plain_pw:
        plain_pw = _gen_password()
        generated = plain_pw

    user = User(
        username=payload.username,
        hashed_password=hash_password(plain_pw),
        is_admin=payload.is_admin,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return CreateUserResponse(user=UserAdminOut.model_validate(user), generated_password=generated)


@router.patch("/users/{user_id}", response_model=UserAdminOut)
async def update_user(
    user_id: int,
    payload: UpdateUserRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == current_admin.id and payload.is_admin is False:
        raise HTTPException(status_code=400, detail="不能取消自己的管理员权限")
    if payload.is_active is not None:
        if user.id == current_admin.id and not payload.is_active:
            raise HTTPException(status_code=400, detail="不能禁用自己的账号")
        user.is_active = payload.is_active
    if payload.is_admin is not None:
        user.is_admin = payload.is_admin
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/users/{user_id}/reset-password", response_model=CreateUserResponse)
async def reset_password(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    new_pw = _gen_password()
    user.hashed_password = hash_password(new_pw)
    await db.commit()
    await db.refresh(user)
    return CreateUserResponse(user=UserAdminOut.model_validate(user), generated_password=new_pw)


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己的账号")
    await db.delete(user)
    await db.commit()
    return MessageResponse(message="已删除")
