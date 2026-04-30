"""Qdrant 向量库封装（local 内嵌 + remote 服务双模式）。

⚠️ local 模式注意：
qdrant-client 的本地模式基于本地文件锁，**同一时刻只能被一个进程打开**。
如果 API 和 Celery Worker 同时启动，会报 "Storage folder ... is already accessed"。
解决方案二选一：
  1) 开发期不启 Celery，把入库改为 API 进程内同步执行
  2) 早一步切到 remote 模式（QDRANT_MODE=remote + 本地起一个 qdrant 服务）
生产部署一律使用 remote 模式。
"""
from __future__ import annotations

import uuid
from typing import Any
from uuid import UUID

from loguru import logger
from pydantic import BaseModel, Field
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchAny,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.core.config import settings
from app.core.exceptions import VectorStoreError


# ===== 数据结构 =====


class PointPayload(BaseModel):
    """要写入向量库的一条记录。"""

    point_id: UUID = Field(default_factory=uuid.uuid4)
    vector: list[float]
    text: str
    doc_id: int
    kb_id: int
    chunk_idx: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    """检索结果。"""

    point_id: UUID
    score: float
    text: str
    doc_id: int
    kb_id: int
    chunk_idx: int
    metadata: dict[str, Any]


# ===== 核心封装 =====


class VectorStore:
    """Qdrant 客户端薄封装，对外暴露语义清晰的方法。"""

    def __init__(self, client: AsyncQdrantClient):
        self._client = client

    @staticmethod
    def collection_name(kb_id: int) -> str:
        """KB id → Qdrant collection 名。"""
        return f"kb_{kb_id}"

    # -------- Collection 管理 --------

    async def collection_exists(self, name: str) -> bool:
        try:
            colls = await self._client.get_collections()
        except Exception as e:
            logger.error("Qdrant get_collections 失败: {}", e)
            raise VectorStoreError(f"列出 collections 失败: {e}") from e
        return any(c.name == name for c in colls.collections)

    async def ensure_collection(self, name: str, dimension: int) -> None:
        """幂等创建 collection。已存在则跳过（不校验维度）。"""
        if await self.collection_exists(name):
            logger.debug("Collection {} 已存在，跳过创建", name)
            return
        try:
            await self._client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
            )
            logger.info("已创建 Qdrant collection: {} (dim={})", name, dimension)
        except Exception as e:
            logger.error("创建 collection 失败: {}", e)
            raise VectorStoreError(f"创建 collection 失败: {e}") from e

    async def delete_collection(self, name: str) -> None:
        try:
            await self._client.delete_collection(collection_name=name)
            logger.info("已删除 Qdrant collection: {}", name)
        except Exception as e:
            # 删除失败不致命（可能本来就不存在）
            logger.warning("删除 collection 失败（可能不存在）: {}", e)

    # -------- Point 数据 --------

    async def upsert_points(
        self,
        collection: str,
        points: list[PointPayload],
    ) -> list[UUID]:
        """批量写入向量+payload。返回写入的 point_id 列表。"""
        if not points:
            return []
        qdrant_points = [
            PointStruct(
                id=str(p.point_id),
                vector=p.vector,
                payload={
                    "doc_id": p.doc_id,
                    "kb_id": p.kb_id,
                    "chunk_idx": p.chunk_idx,
                    "text": p.text,
                    "metadata": p.metadata,
                },
            )
            for p in points
        ]
        try:
            await self._client.upsert(collection_name=collection, points=qdrant_points)
        except Exception as e:
            logger.error("Qdrant upsert 失败: {}", e)
            raise VectorStoreError(f"写入向量失败: {e}") from e
        logger.debug("已写入 {} 个 points 到 {}", len(points), collection)
        return [p.point_id for p in points]

    async def search(
        self,
        collection: str,
        query_vector: list[float],
        top_k: int = 20,
        doc_ids: list[int] | None = None,
    ) -> list[SearchResult]:
        """向量检索；可按 doc_ids 过滤（仅在该文档范围内搜）。"""
        query_filter = self._build_doc_filter(doc_ids)

        try:
            # qdrant-client 1.10+ 推荐使用 query_points（替代已弃用的 search）
            response = await self._client.query_points(
                collection_name=collection,
                query=query_vector,
                limit=top_k,
                query_filter=query_filter,
                with_payload=True,
            )
        except Exception as e:
            logger.error("Qdrant query_points 失败: {}", e)
            raise VectorStoreError(f"检索失败: {e}") from e

        hits = response.points
        if hits:
            logger.debug(
                "Qdrant 原始分数 top-5: {}",
                [round(float(h.score), 4) for h in hits[:5]],
            )
        results: list[SearchResult] = []
        for h in hits:
            payload = h.payload or {}
            results.append(
                SearchResult(
                    point_id=UUID(str(h.id)),
                    score=float(h.score),
                    text=payload.get("text", ""),
                    doc_id=int(payload.get("doc_id", 0)),
                    kb_id=int(payload.get("kb_id", 0)),
                    chunk_idx=int(payload.get("chunk_idx", 0)),
                    metadata=payload.get("metadata") or {},
                )
            )
        return results

    async def delete_by_doc_id(self, collection: str, doc_id: int) -> None:
        """删除某文档在 collection 中的所有 points。"""
        try:
            await self._client.delete(
                collection_name=collection,
                points_selector=FilterSelector(
                    filter=Filter(
                        must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
                    )
                ),
            )
            logger.info("已删除 collection={} 中 doc_id={} 的所有 points", collection, doc_id)
        except Exception as e:
            logger.error("删除 points 失败: {}", e)
            raise VectorStoreError(f"删除向量失败: {e}") from e

    async def count(self, collection: str) -> int:
        """统计 collection 中 point 总数（调试用）。"""
        try:
            res = await self._client.count(collection_name=collection, exact=True)
            return int(res.count)
        except Exception as e:
            logger.warning("count 失败: {}", e)
            return 0

    async def close(self) -> None:
        await self._client.close()

    # -------- 内部 --------

    @staticmethod
    def _build_doc_filter(doc_ids: list[int] | None) -> Filter | None:
        if not doc_ids:
            return None
        if len(doc_ids) == 1:
            match: Any = MatchValue(value=doc_ids[0])
        else:
            match = MatchAny(any=doc_ids)
        return Filter(must=[FieldCondition(key="doc_id", match=match)])


# ===== 工厂（单例）=====

_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is not None:
        return _store

    if settings.QDRANT_MODE == "local":
        client = AsyncQdrantClient(path=str(settings.qdrant_local_path_resolved))
        logger.info("Qdrant 启用 local 模式: {}", settings.qdrant_local_path_resolved)
    else:
        client = AsyncQdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            api_key=settings.QDRANT_API_KEY or None,
        )
        logger.info(
            "Qdrant 启用 remote 模式: {}:{}", settings.QDRANT_HOST, settings.QDRANT_PORT
        )

    _store = VectorStore(client)
    return _store


async def reset_vector_store() -> None:
    """清除单例（测试或切换配置时用）。"""
    global _store
    if _store is not None:
        await _store.close()
        _store = None
