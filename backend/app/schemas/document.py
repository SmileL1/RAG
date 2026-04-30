"""文档相关 DTO。"""
from __future__ import annotations

from datetime import datetime

from app.schemas.common import TimestampOut


class DocumentOut(TimestampOut):
    id: int
    kb_id: int
    filename: str
    file_size: int
    mime_type: str | None
    status: str
    error_message: str | None
    chunk_count: int
    processed_at: datetime | None


class DocumentStatusOut(TimestampOut):
    id: int
    status: str
    chunk_count: int
    error_message: str | None
    processed_at: datetime | None
