"""VectorStore 集成测试：使用 qdrant-client 内存模式跑真实流程。"""
from __future__ import annotations

import pytest
import pytest_asyncio
from qdrant_client import AsyncQdrantClient

from app.rag.vector_store import PointPayload, VectorStore


@pytest_asyncio.fixture
async def store():
    client = AsyncQdrantClient(":memory:")
    s = VectorStore(client)
    yield s
    await client.close()


@pytest.mark.asyncio
async def test_collection_lifecycle(store: VectorStore):
    name = "kb_lifecycle"
    assert await store.collection_exists(name) is False

    await store.ensure_collection(name, dimension=4)
    assert await store.collection_exists(name) is True

    # 幂等：再调一次不抛
    await store.ensure_collection(name, dimension=4)

    await store.delete_collection(name)
    assert await store.collection_exists(name) is False


@pytest.mark.asyncio
async def test_upsert_empty_returns_empty(store: VectorStore):
    result = await store.upsert_points("any", [])
    assert result == []


@pytest.mark.asyncio
async def test_upsert_and_search_basic(store: VectorStore):
    name = "kb_search"
    await store.ensure_collection(name, dimension=4)

    points = [
        PointPayload(
            vector=[1.0, 0.0, 0.0, 0.0], text="第一段", doc_id=1, kb_id=1, chunk_idx=0,
        ),
        PointPayload(
            vector=[0.0, 1.0, 0.0, 0.0], text="第二段", doc_id=1, kb_id=1, chunk_idx=1,
        ),
        PointPayload(
            vector=[0.0, 0.0, 1.0, 0.0],
            text="第三段（来自 doc 2）",
            doc_id=2,
            kb_id=1,
            chunk_idx=0,
            metadata={"page": 5},
        ),
    ]
    ids = await store.upsert_points(name, points)
    assert len(ids) == 3

    # 搜 [1,0,0,0]，第一段最相似
    results = await store.search(name, [1.0, 0.0, 0.0, 0.0], top_k=3)
    assert len(results) == 3
    assert results[0].text == "第一段"
    assert results[0].score > 0.99
    # 元数据透传
    third_hit = next(r for r in results if r.doc_id == 2)
    assert third_hit.metadata == {"page": 5}


@pytest.mark.asyncio
async def test_search_with_doc_id_filter(store: VectorStore):
    name = "kb_filter"
    await store.ensure_collection(name, dimension=2)
    await store.upsert_points(
        name,
        [
            PointPayload(vector=[1.0, 0.0], text="d1c0", doc_id=1, kb_id=1, chunk_idx=0),
            PointPayload(vector=[0.0, 1.0], text="d1c1", doc_id=1, kb_id=1, chunk_idx=1),
            PointPayload(vector=[1.0, 1.0], text="d2c0", doc_id=2, kb_id=1, chunk_idx=0),
            PointPayload(vector=[0.5, 0.5], text="d3c0", doc_id=3, kb_id=1, chunk_idx=0),
        ],
    )

    # 单 doc_id
    results = await store.search(name, [1.0, 0.0], top_k=10, doc_ids=[2])
    assert len(results) == 1
    assert results[0].doc_id == 2

    # 多 doc_id（OR 关系）
    results = await store.search(name, [1.0, 0.0], top_k=10, doc_ids=[1, 3])
    doc_ids_returned = {r.doc_id for r in results}
    assert doc_ids_returned == {1, 3}


@pytest.mark.asyncio
async def test_delete_by_doc_id(store: VectorStore):
    name = "kb_delete"
    await store.ensure_collection(name, dimension=2)
    await store.upsert_points(
        name,
        [
            PointPayload(vector=[1.0, 0.0], text="a", doc_id=1, kb_id=1, chunk_idx=0),
            PointPayload(vector=[0.0, 1.0], text="b", doc_id=1, kb_id=1, chunk_idx=1),
            PointPayload(vector=[1.0, 1.0], text="c", doc_id=2, kb_id=1, chunk_idx=0),
        ],
    )

    assert await store.count(name) == 3

    await store.delete_by_doc_id(name, doc_id=1)

    assert await store.count(name) == 1
    results = await store.search(name, [1.0, 1.0], top_k=10)
    assert len(results) == 1
    assert results[0].doc_id == 2


@pytest.mark.asyncio
async def test_collection_name_helper():
    assert VectorStore.collection_name(1) == "kb_1"
    assert VectorStore.collection_name(42) == "kb_42"


@pytest.mark.asyncio
async def test_search_filter_no_match_returns_empty(store: VectorStore):
    name = "kb_nomatch"
    await store.ensure_collection(name, dimension=2)
    await store.upsert_points(
        name,
        [PointPayload(vector=[1.0, 0.0], text="a", doc_id=1, kb_id=1, chunk_idx=0)],
    )
    results = await store.search(name, [1.0, 0.0], top_k=5, doc_ids=[999])
    assert results == []
