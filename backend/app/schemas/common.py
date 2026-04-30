"""通用 Pydantic 模型。"""
from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ORMModel(BaseModel):
    """从 SQLAlchemy ORM 实例转 Pydantic。"""

    model_config = ConfigDict(from_attributes=True)


class TimestampOut(ORMModel):
    created_at: datetime
    updated_at: datetime


class PageResult(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int = 1
    page_size: int = 20


class MessageResponse(BaseModel):
    message: str
