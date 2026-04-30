"""文档处理 Celery 任务。"""
from __future__ import annotations

import asyncio

from loguru import logger

from app.tasks.celery_app import celery_app


@celery_app.task(
    name="document.process",
    bind=True,
    max_retries=2,
    default_retry_delay=10,
)
def process_document(self, document_id: int) -> dict:
    """异步处理一个文档：解析→分块→嵌入→入库。"""
    try:
        chunk_count = asyncio.run(_process_async(document_id))
        return {
            "document_id": document_id,
            "chunk_count": chunk_count,
            "status": "ready",
        }
    except Exception as e:
        logger.exception("Celery 任务失败 doc_id={}: {}", document_id, e)
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            return {
                "document_id": document_id,
                "status": "failed",
                "error": str(e),
            }


async def _process_async(document_id: int) -> int:
    from app.core.database import AsyncSessionLocal
    from app.rag.ingestion import get_ingestion_service

    service = get_ingestion_service()
    async with AsyncSessionLocal() as db:
        return await service.ingest(db, document_id)
