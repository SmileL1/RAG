"""检索服务：query → embedding → vector search → (rerank) → Top-K。

流程：
  1. 把 query embedding 化（可选 HyDE：先让 LLM 生成假答案，用假答案 embedding）
  2. Qdrant 召回 retrieve_top_k（默认 20）个候选
  3. 若启用 reranker：对候选精排，取 Top-K（默认 5）
  4. 否则：直接取 Top-K
返回 SearchResult 列表，按相关度降序。
"""
from __future__ import annotations

import asyncio

from loguru import logger

from app.core.config import settings
from app.rag.embedders.base import BaseEmbedder
from app.rag.rerank import BaseReranker
from app.rag.vector_store import SearchResult, VectorStore


class RetrievalService:
    def __init__(
        self,
        embedder: BaseEmbedder,
        vector_store: VectorStore,
        reranker: BaseReranker | None = None,
        retrieve_top_k: int = 20,
        rerank_top_k: int = 5,
    ):
        self._embedder = embedder
        self._vector_store = vector_store
        self._reranker = reranker
        self._retrieve_top_k = retrieve_top_k
        self._rerank_top_k = rerank_top_k

    async def retrieve(
        self,
        query: str,
        kb_id: int,
        *,
        doc_ids: list[int] | None = None,
        top_k: int | None = None,
    ) -> list[SearchResult]:
        if not query or not query.strip():
            return []

        final_top_k = top_k or self._rerank_top_k
        recall_k = max(self._retrieve_top_k, final_top_k * 2)

        query_vector = await self._embedder.embed_query(query)

        collection = VectorStore.collection_name(kb_id)
        candidates = await self._vector_store.search(
            collection=collection,
            query_vector=query_vector,
            top_k=recall_k,
            doc_ids=doc_ids,
        )
        logger.debug(
            "Retrieval: query='{}' kb={} 召回 {} 条候选",
            query[:30],
            kb_id,
            len(candidates),
        )

        if not candidates:
            return []

        if self._reranker is not None:
            ranked = await self._reranker.rerank(query, candidates, top_k=final_top_k)
            logger.debug("Retrieval: 重排后取 Top-{}", len(ranked))
            return ranked

        return candidates[:final_top_k]

    async def retrieve_stream(
        self,
        query: str,
        kb_id: int,
        *,
        doc_ids: list[int] | None = None,
        top_k: int | None = None,
    ) -> tuple[list[SearchResult], asyncio.Task[list[SearchResult]] | None]:
        """流式生成专用：向量搜索立即返回，rerank 作为后台 Task 并行执行。

        返回 (raw_top_k, rerank_task)：
        - raw_top_k   ：Qdrant 原始 top-K，用于立即构建 LLM prompt
        - rerank_task ：后台 rerank 任务（None 表示未启用 reranker），
                        在 LLM 流式生成完毕后 await，得到最终排序的 citations
        """
        if not query or not query.strip():
            return [], None

        final_top_k = top_k or self._rerank_top_k
        recall_k = max(self._retrieve_top_k, final_top_k * 2)

        query_vector = await self._embedder.embed_query(query)

        collection = VectorStore.collection_name(kb_id)
        candidates = await self._vector_store.search(
            collection=collection,
            query_vector=query_vector,
            top_k=recall_k,
            doc_ids=doc_ids,
        )
        logger.debug(
            "Retrieval(stream): query='{}' kb={} 召回 {} 条候选",
            query[:30],
            kb_id,
            len(candidates),
        )

        if not candidates:
            return [], None

        raw_top = candidates[:final_top_k]

        if self._reranker is not None:
            task: asyncio.Task[list[SearchResult]] = asyncio.create_task(
                self._reranker.rerank(query, candidates, top_k=final_top_k)
            )
            return raw_top, task

        return raw_top, None


# ===== 工厂 =====


def get_retrieval_service() -> RetrievalService:
    from app.rag.embedders.factory import get_embedder
    from app.rag.rerank import get_reranker
    from app.rag.vector_store import get_vector_store

    return RetrievalService(
        embedder=get_embedder(),
        vector_store=get_vector_store(),
        reranker=get_reranker(),
        retrieve_top_k=settings.RETRIEVE_TOP_K,
        rerank_top_k=settings.RERANK_TOP_K,
    )
