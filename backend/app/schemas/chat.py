"""对话相关 DTO。"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import TimestampOut


class ChatRequest(BaseModel):
    kb_id: int
    question: str = Field(..., min_length=1, max_length=4000)
    conversation_id: int | None = None
    use_hyde: bool | None = None  # 覆盖全局配置


class Citation(BaseModel):
    doc_id: int
    filename: str
    page: int | None = None
    chunk_idx: int
    text: str
    score: float | None = None


class TokenEvent(BaseModel):
    """SSE token 事件。"""

    content: str


class CitationEvent(BaseModel):
    """SSE citation 事件。"""

    citations: list[Citation]


class DoneEvent(BaseModel):
    """SSE done 事件。"""

    message_id: int
    conversation_id: int


class ConversationOut(TimestampOut):
    id: int
    kb_id: int | None
    title: str | None


class MessageOut(TimestampOut):
    id: int
    conversation_id: int
    role: str
    content: str
    citations: list[dict[str, Any]] | None
    tokens_used: int | None
