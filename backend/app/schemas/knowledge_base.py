"""知识库相关 DTO。"""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import TimestampOut


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = None


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=128)
    description: str | None = None


class KnowledgeBaseOut(TimestampOut):
    id: int
    name: str
    description: str | None
    embedding_model: str
    embedding_dim: int
