"""IngestionService 测试：用真实 Chunker + 内存 Qdrant + FakeEmbedder + Mock DB。"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from qdrant_client import AsyncQdrantClient

from app.models.document import DocumentStatus
from app.rag.chunker import Chunker
from app.rag.embedders.base import BaseEmbedder
from app.rag.ingestion import IngestionService
from app.rag.vector_store import VectorStore


class FakeEmbedder(BaseEmbedder):
    name = "fake-embedder"
    dimension = 4

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        # 返回稳定但不同的向量
        return [[float(i + 1), 0.0, 0.0, 0.0] for i in range(len(texts))]

    async def embed_query(self, query: str) -> list[float]:
        return [1.0, 0.0, 0.0, 0.0]


@pytest_asyncio.fixture
async def store():
    client = AsyncQdrantClient(":memory:")
    yield VectorStore(client)
    await client.close()


def _make_fake_db(doc, kb):
    """构造一个最小可用的 mock AsyncSession。"""
    db = MagicMock()
    db.get = AsyncMock(side_effect=[doc, kb])
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.rollback = AsyncMock()
    db.add_all = MagicMock()
    return db


@pytest.mark.asyncio
async def test_ingestion_happy_path(tmp_path: Path, store: VectorStore):
    src = tmp_path / "doc.txt"
    src.write_text("第一段内容。\n\n第二段内容。\n\n第三段内容。", encoding="utf-8")

    fake_doc = MagicMock(
        id=42,
        kb_id=7,
        file_path=str(src),
        status=DocumentStatus.PENDING.value,
        error_message=None,
        chunk_count=0,
        processed_at=None,
    )
    fake_kb = MagicMock(id=7, collection_name="kb_7")
    db = _make_fake_db(fake_doc, fake_kb)

    service = IngestionService(
        chunker=Chunker(chunk_size=512, chunk_overlap=10),
        embedder=FakeEmbedder(),
        vector_store=store,
    )

    chunk_count = await service.ingest(db, 42)

    assert chunk_count >= 1
    assert fake_doc.status == DocumentStatus.READY.value
    assert fake_doc.chunk_count == chunk_count
    assert isinstance(fake_doc.processed_at, datetime)

    # Qdrant 真的写入了
    assert await store.count("kb_7") == chunk_count
    db.add_all.assert_called_once()


@pytest.mark.asyncio
async def test_ingestion_marks_failed_on_missing_file(tmp_path: Path, store: VectorStore):
    fake_doc = MagicMock(
        id=1,
        kb_id=1,
        file_path=str(tmp_path / "nonexistent.txt"),
        status=DocumentStatus.PENDING.value,
        error_message=None,
    )
    fake_kb = MagicMock(id=1, collection_name="kb_1")
    db = _make_fake_db(fake_doc, fake_kb)

    service = IngestionService(
        chunker=Chunker(),
        embedder=FakeEmbedder(),
        vector_store=store,
    )

    with pytest.raises(Exception, match="文件不存在"):
        await service.ingest(db, 1)

    assert fake_doc.status == DocumentStatus.FAILED.value
    assert "不存在" in (fake_doc.error_message or "")


@pytest.mark.asyncio
async def test_ingestion_marks_failed_on_unsupported_ext(tmp_path: Path, store: VectorStore):
    src = tmp_path / "doc.xyz"
    src.write_text("noop", encoding="utf-8")

    fake_doc = MagicMock(id=1, kb_id=1, file_path=str(src), status="pending")
    fake_kb = MagicMock(id=1, collection_name="kb_1")
    db = _make_fake_db(fake_doc, fake_kb)

    service = IngestionService(
        chunker=Chunker(),
        embedder=FakeEmbedder(),
        vector_store=store,
    )

    with pytest.raises(Exception):
        await service.ingest(db, 1)

    assert fake_doc.status == DocumentStatus.FAILED.value


@pytest.mark.asyncio
async def test_ingestion_doc_not_found(store: VectorStore):
    db = MagicMock()
    db.get = AsyncMock(return_value=None)
    db.commit = AsyncMock()

    service = IngestionService(
        chunker=Chunker(),
        embedder=FakeEmbedder(),
        vector_store=store,
    )
    with pytest.raises(Exception, match="文档"):
        await service.ingest(db, 999)
