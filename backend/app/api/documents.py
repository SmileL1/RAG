"""文档路由：上传、列表、状态、预览、删除（删除已联动 Qdrant）。"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.exceptions import AppException
from app.models.chunk import Chunk
from app.models.document import Document
from app.rag.ingestion import get_ingestion_service
from app.rag.vector_store import VectorStore, get_vector_store
from app.schemas.common import MessageResponse
from app.schemas.document import DocumentOut, DocumentStatusOut
from app.services.document_service import DocumentService

router = APIRouter(
    prefix="/api",
    tags=["documents"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/kb/{kb_id}/documents",
    response_model=DocumentOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    kb_id: int,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """上传文档；立即返回 pending，异步解析+入库。"""
    doc = await DocumentService.upload(db, kb_id, file)

    if settings.INGEST_MODE == "celery":
        # 提交到 Celery（生产模式，要求 QDRANT_MODE=remote）
        from app.tasks.document_tasks import process_document

        process_document.delay(doc.id)
        logger.info("已提交 Celery 任务 doc_id={}", doc.id)
    else:
        # 默认 sync：BackgroundTasks 在 API 进程异步执行
        background_tasks.add_task(_ingest_in_background, doc.id)

    return doc


async def _ingest_in_background(document_id: int) -> None:
    """API 进程内异步执行入库（不阻塞响应）。"""
    service = get_ingestion_service()
    async with AsyncSessionLocal() as db:
        try:
            await service.ingest(db, document_id)
        except Exception as e:
            logger.error("BackgroundTasks 入库失败 doc_id={}: {}", document_id, e)


@router.get("/kb/{kb_id}/documents", response_model=list[DocumentOut])
async def list_documents(kb_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Document).where(Document.kb_id == kb_id).order_by(Document.id.desc())
    )
    return result.scalars().all()


@router.get("/documents/{doc_id}", response_model=DocumentOut)
async def get_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "文档不存在")
    return doc


@router.get("/documents/{doc_id}/status", response_model=DocumentStatusOut)
async def get_document_status(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "文档不存在")
    return doc


@router.get("/documents/{doc_id}/text")
async def get_document_text(doc_id: int, db: AsyncSession = Depends(get_db)):
    """返回文档所有 chunk 的文本内容（用于前端预览）。"""
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "文档不存在")
    result = await db.execute(
        select(Chunk).where(Chunk.document_id == doc_id).order_by(Chunk.chunk_idx)
    )
    chunks = result.scalars().all()
    content = "\n\n---\n\n".join(c.content for c in chunks)
    return {"filename": doc.filename, "content": content, "chunk_count": len(chunks)}


@router.get("/documents/{doc_id}/raw")
async def get_document_raw(doc_id: int, db: AsyncSession = Depends(get_db)):
    """返回原始文件流（用于在浏览器内联预览 PDF / TXT 等）。"""
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "文档不存在")
    path = Path(doc.file_path)
    if not path.exists():
        raise HTTPException(404, "文件已从磁盘删除")
    return FileResponse(
        path=str(path),
        filename=doc.filename,
        media_type=doc.mime_type or "application/octet-stream",
        content_disposition_type="inline",
    )


@router.delete("/documents/{doc_id}", response_model=MessageResponse)
async def delete_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "文档不存在")
    kb_id = doc.kb_id
    await db.delete(doc)
    await db.commit()

    store = get_vector_store()
    await store.delete_by_doc_id(VectorStore.collection_name(kb_id), doc_id=doc_id)
    logger.info("文档已删除 id={} (kb={})", doc_id, kb_id)
    return MessageResponse(message="已删除")
