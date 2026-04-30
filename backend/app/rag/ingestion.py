"""文档入库服务：解析 → 分块 → 嵌入 → 写 Qdrant + chunks 表。

负责把一个已落盘的 Document 完整加工入库，最后把 status 置为 ready/failed。
本服务**不感知** sync vs celery，被 BackgroundTasks 或 Celery Worker 复用。
"""
from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException, NotFoundError
from app.models.chunk import Chunk
from app.models.document import Document, DocumentStatus
from app.models.knowledge_base import KnowledgeBase
from app.rag.chunker import Chunker
from app.rag.embedders.base import BaseEmbedder
from app.rag.parsers.factory import get_parser
from app.rag.vector_store import PointPayload, VectorStore


class IngestionService:
    def __init__(
        self,
        chunker: Chunker,
        embedder: BaseEmbedder,
        vector_store: VectorStore,
    ):
        self._chunker = chunker
        self._embedder = embedder
        self._vector_store = vector_store

    async def ingest(self, db: AsyncSession, document_id: int) -> int:
        """完整入库流水线，返回入库的 chunk 数；失败时设置 doc.status=failed 并抛异常。"""
        doc = await db.get(Document, document_id)
        if not doc:
            raise NotFoundError(f"文档 {document_id} 不存在")
        kb = await db.get(KnowledgeBase, doc.kb_id)
        if not kb:
            raise NotFoundError(f"知识库 {doc.kb_id} 不存在")

        doc.status = DocumentStatus.PROCESSING.value
        doc.error_message = None
        await db.commit()

        try:
            chunk_count = await self._do_ingest(db, doc, kb)
            doc.status = DocumentStatus.READY.value
            doc.chunk_count = chunk_count
            doc.processed_at = datetime.now()
            await db.commit()
            logger.info("文档入库成功 doc_id={} chunks={}", doc.id, chunk_count)
            return chunk_count
        except Exception as e:
            logger.exception("文档入库失败 doc_id={}: {}", doc.id, e)
            doc.status = DocumentStatus.FAILED.value
            doc.error_message = str(e)[:1000]
            try:
                await db.commit()
            except Exception:
                await db.rollback()
            raise

    async def _do_ingest(
        self,
        db: AsyncSession,
        doc: Document,
        kb: KnowledgeBase,
    ) -> int:
        # 1. 解析
        file_path = Path(doc.file_path)
        if not file_path.exists():
            raise AppException(f"文件不存在: {file_path}")
        ext = file_path.suffix.lower()
        parser = get_parser(ext)
        segments = await parser.parse(file_path)
        if not segments:
            raise AppException("文档解析为空（可能是扫描版 PDF 或文件损坏）")

        # 2. 分块
        chunks = self._chunker.chunk(segments)
        if not chunks:
            raise AppException("分块结果为空")

        # 3. 嵌入
        texts = [c.text for c in chunks]
        vectors = await self._embedder.embed_texts(texts)
        if len(vectors) != len(chunks):
            raise AppException(
                f"Embedding 数量不匹配: chunks={len(chunks)} vectors={len(vectors)}"
            )

        # 4. 准备 Qdrant point + chunks 表行
        collection = kb.collection_name
        point_payloads: list[PointPayload] = []
        chunk_rows: list[Chunk] = []
        for i, (c, v) in enumerate(zip(chunks, vectors, strict=True)):
            point_id = uuid.uuid4()
            point_payloads.append(
                PointPayload(
                    point_id=point_id,
                    vector=v,
                    text=c.text,
                    doc_id=doc.id,
                    kb_id=kb.id,
                    chunk_idx=i,
                    metadata=c.metadata,
                )
            )
            chunk_rows.append(
                Chunk(
                    document_id=doc.id,
                    chunk_idx=i,
                    content=c.text,
                    chunk_metadata=c.metadata,
                    qdrant_point_id=point_id,
                )
            )

        # 5. 写 Qdrant（先确保 collection 存在）
        await self._vector_store.ensure_collection(
            collection, dimension=self._embedder.dimension
        )
        await self._vector_store.upsert_points(collection, point_payloads)

        # 6. 写 chunks 表
        db.add_all(chunk_rows)
        await db.flush()

        return len(chunks)


def get_ingestion_service() -> IngestionService:
    """构造单次使用的服务实例（embedder / vector_store 内部已是单例）。"""
    from app.rag.embedders.factory import get_embedder
    from app.rag.vector_store import get_vector_store

    return IngestionService(
        chunker=Chunker(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        ),
        embedder=get_embedder(),
        vector_store=get_vector_store(),
    )
