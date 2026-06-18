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


@router.get("/documents/{doc_id}/chunk-context")
async def get_chunk_context(
    doc_id: int,
    idx: int,
    window: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """返回指定 chunk_idx 及其前后 window 个片段，供原文溯源查看上下文。"""
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "文档不存在")
    window = max(0, min(window, 3))
    lo, hi = idx - window, idx + window
    result = await db.execute(
        select(Chunk)
        .where(Chunk.document_id == doc_id, Chunk.chunk_idx >= lo, Chunk.chunk_idx <= hi)
        .order_by(Chunk.chunk_idx)
    )
    chunks = result.scalars().all()
    return {
        "filename": doc.filename,
        "doc_id": doc_id,
        "target_idx": idx,
        "chunks": [
            {"chunk_idx": c.chunk_idx, "content": c.content, "is_hit": c.chunk_idx == idx}
            for c in chunks
        ],
    }


@router.get("/documents/{doc_id}/chunks")
async def get_document_chunks(doc_id: int, db: AsyncSession = Depends(get_db)):
    """返回文档全部片段（按 chunk_idx 排序），供溯源在全文中精确定位高亮命中段。"""
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "文档不存在")
    result = await db.execute(
        select(Chunk).where(Chunk.document_id == doc_id).order_by(Chunk.chunk_idx)
    )
    chunks = result.scalars().all()
    return {
        "filename": doc.filename,
        "doc_id": doc_id,
        "chunks": [{"chunk_idx": c.chunk_idx, "content": c.content} for c in chunks],
    }


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


@router.post("/documents/{doc_id}/retry", response_model=DocumentOut)
async def retry_document(
    doc_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """重新触发失败文档的解析入库。清除旧 chunks 和向量后重新排队。"""
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "文档不存在")
    if doc.status not in ("failed", "pending"):
        raise HTTPException(400, f"只有 failed/pending 状态可重试，当前状态: {doc.status}")
    if not Path(doc.file_path).exists():
        raise HTTPException(404, "原始文件已从磁盘删除，无法重试")

    # 清除旧 chunks 和向量
    old_chunks = await db.execute(
        select(Chunk).where(Chunk.document_id == doc_id)
    )
    for chunk in old_chunks.scalars().all():
        await db.delete(chunk)
    store = get_vector_store()
    await store.delete_by_doc_id(VectorStore.collection_name(doc.kb_id), doc_id=doc_id)

    # 重置状态
    doc.status = "pending"
    doc.error_message = None
    doc.chunk_count = 0
    doc.processed_at = None
    await db.commit()
    await db.refresh(doc)

    if settings.INGEST_MODE == "celery":
        from app.tasks.document_tasks import process_document
        process_document.delay(doc.id)
    else:
        background_tasks.add_task(_ingest_in_background, doc.id)

    logger.info("文档重试已触发 doc_id={}", doc_id)
    return doc


async def _reset_for_reingest(db: AsyncSession, doc: Document) -> None:
    """清除某文档的旧 chunks + 向量，并把状态重置为 pending（为重新入库做准备）。"""
    old_chunks = await db.execute(select(Chunk).where(Chunk.document_id == doc.id))
    for chunk in old_chunks.scalars().all():
        await db.delete(chunk)
    store = get_vector_store()
    await store.delete_by_doc_id(VectorStore.collection_name(doc.kb_id), doc_id=doc.id)
    doc.status = "pending"
    doc.error_message = None
    doc.chunk_count = 0
    doc.processed_at = None


@router.post("/documents/{doc_id}/reindex", response_model=DocumentOut)
async def reindex_document(
    doc_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """重新切块入库（任意状态可用，含已 ready 的文档）。清旧 chunks/向量后重排。"""
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "文档不存在")
    if not Path(doc.file_path).exists():
        raise HTTPException(404, "原始文件已从磁盘删除，无法重新索引")

    await _reset_for_reingest(db, doc)
    await db.commit()
    await db.refresh(doc)

    if settings.INGEST_MODE == "celery":
        from app.tasks.document_tasks import process_document
        process_document.delay(doc.id)
    else:
        background_tasks.add_task(_ingest_in_background, doc.id)

    logger.info("文档重新索引已触发 doc_id={}", doc_id)
    return doc


@router.post("/documents/reindex-all")
async def reindex_all_documents(
    background_tasks: BackgroundTasks,
    kb_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """批量重新索引（可选按 kb_id 过滤）。逐个清旧数据并排队重排，返回触发数量。"""
    stmt = select(Document)
    if kb_id is not None:
        stmt = stmt.where(Document.kb_id == kb_id)
    docs = (await db.execute(stmt)).scalars().all()

    triggered, skipped = 0, 0
    queued_ids: list[int] = []
    for doc in docs:
        if not Path(doc.file_path).exists():
            skipped += 1
            continue
        await _reset_for_reingest(db, doc)
        queued_ids.append(doc.id)
        triggered += 1
    await db.commit()

    for did in queued_ids:
        if settings.INGEST_MODE == "celery":
            from app.tasks.document_tasks import process_document
            process_document.delay(did)
        else:
            background_tasks.add_task(_ingest_in_background, did)

    logger.info("批量重新索引：触发 {} 个，跳过 {} 个（文件缺失）", triggered, skipped)
    return {"triggered": triggered, "skipped": skipped, "total": len(docs)}


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
