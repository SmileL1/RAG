"""文档业务服务：上传文件落盘 + 建 DB 记录。"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import UploadFile
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    FileTooLargeError,
    NotFoundError,
    UnsupportedFileTypeError,
)
from app.models.document import Document, DocumentStatus
from app.models.knowledge_base import KnowledgeBase
from app.rag.parsers.factory import supported_extensions


class DocumentService:
    @staticmethod
    async def upload(
        db: AsyncSession,
        kb_id: int,
        upload_file: UploadFile,
    ) -> Document:
        kb = await db.get(KnowledgeBase, kb_id)
        if not kb:
            raise NotFoundError("知识库不存在")

        original_name = upload_file.filename or "untitled"
        ext = Path(original_name).suffix.lower()
        if ext not in supported_extensions():
            raise UnsupportedFileTypeError(f"不支持的文件类型: {ext}")

        # 读入内存判断大小（>100MB 文件应该走流式落盘，留作后续优化）
        content = await upload_file.read()
        size = len(content)
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if size > max_bytes:
            raise FileTooLargeError(
                f"文件超过 {settings.MAX_FILE_SIZE_MB}MB 限制（当前 {size / 1024 / 1024:.1f}MB）"
            )

        # 落盘到 uploads/kb_<id>/<uuid8>_<原名>
        kb_dir = settings.upload_dir_path / f"kb_{kb_id}"
        kb_dir.mkdir(parents=True, exist_ok=True)
        unique_name = f"{uuid.uuid4().hex[:8]}_{original_name}"
        dest = kb_dir / unique_name
        dest.write_bytes(content)

        # 建 DB 记录
        doc = Document(
            kb_id=kb_id,
            filename=original_name,
            file_path=str(dest),
            file_size=size,
            mime_type=upload_file.content_type,
            status=DocumentStatus.PENDING.value,
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)

        logger.info(
            "文档已上传 doc_id={} kb_id={} filename={} size={}KB",
            doc.id,
            kb_id,
            original_name,
            size // 1024,
        )
        return doc
