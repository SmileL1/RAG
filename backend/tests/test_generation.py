"""GenerationService 测试：FakeLLM + 真实检索栈（内存 Qdrant + FakeEmbedder）。"""
from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
import pytest_asyncio
from qdrant_client import AsyncQdrantClient

from app.rag.embedders.base import BaseEmbedder
from app.rag.generation import (
    CitationEvent,
    FinalEvent,
    GenerationService,
    TokenEvent,
)
from app.rag.llm.base import BaseLLM
from app.rag.retrieval import RetrievalService
from app.rag.vector_store import PointPayload, VectorStore


class FakeEmbedder(BaseEmbedder):
    name = "fake"
    dimension = 4

    async def embed_texts(self, texts):
        return [[1.0, 0.0, 0.0, 0.0] for _ in texts]

    async def embed_query(self, query):
        return [1.0, 0.0, 0.0, 0.0]


class FakeLLM(BaseLLM):
    name = "fake-llm"

    def __init__(self, tokens: list[str] | None = None):
        self._tokens = tokens or ["年", "假", "是", " ", "15", " ", "天", "。"]
        self.last_messages: list[dict[str, str]] = []

    async def chat(self, messages, **kwargs: Any) -> str:
        self.last_messages = messages
        return "".join(self._tokens)

    async def stream_chat(self, messages, **kwargs: Any) -> AsyncIterator[str]:
        self.last_messages = messages
        for t in self._tokens:
            yield t


@pytest_asyncio.fixture
async def filled_store():
    client = AsyncQdrantClient(":memory:")
    store = VectorStore(client)
    await store.ensure_collection("kb_1", dimension=4)
    await store.upsert_points(
        "kb_1",
        [
            PointPayload(
                vector=[1.0, 0.0, 0.0, 0.0],
                text="员工每年享有 15 天年休假。",
                doc_id=1,
                kb_id=1,
                chunk_idx=0,
                metadata={"filename": "员工手册.pdf", "page": 12},
            ),
            PointPayload(
                vector=[0.95, 0.05, 0.0, 0.0],
                text="试用期员工不享受年休假。",
                doc_id=1,
                kb_id=1,
                chunk_idx=1,
                metadata={"filename": "员工手册.pdf", "page": 12},
            ),
        ],
    )
    yield store
    await client.close()


def _make_generation_service(store: VectorStore, llm: FakeLLM) -> GenerationService:
    retrieval = RetrievalService(
        embedder=FakeEmbedder(),
        vector_store=store,
        reranker=None,
        retrieve_top_k=20,
        rerank_top_k=2,
    )
    return GenerationService(retrieval_service=retrieval, llm=llm, use_hyde=False)


@pytest.mark.asyncio
async def test_stream_answer_emits_token_citation_final(filled_store):
    llm = FakeLLM(["年", "假", "15", "天"])
    svc = _make_generation_service(filled_store, llm)

    events = [ev async for ev in svc.stream_answer("年假是多少天？", kb_id=1)]

    token_events = [e for e in events if isinstance(e, TokenEvent)]
    citation_events = [e for e in events if isinstance(e, CitationEvent)]
    final_events = [e for e in events if isinstance(e, FinalEvent)]

    assert [e.content for e in token_events] == ["年", "假", "15", "天"]
    assert len(citation_events) == 1
    assert len(citation_events[0].citations) == 2
    assert citation_events[0].citations[0].filename == "员工手册.pdf"

    assert len(final_events) == 1
    assert final_events[0].answer == "年假15天"
    assert final_events[0].chunks_used == 2


@pytest.mark.asyncio
async def test_stream_answer_no_match_returns_fallback(filled_store):
    """召回为空时直接返回兜底文案，不打 LLM。"""
    llm = FakeLLM(["不会被调用"])
    # 用空 KB 触发零召回
    empty_store = filled_store
    # 实际上 filled_store 有数据；改用 doc_ids 过滤到不存在的 doc
    svc = _make_generation_service(empty_store, llm)

    events = [
        ev async for ev in svc.stream_answer("xxx", kb_id=1, doc_ids=[999])
    ]

    final = next(e for e in events if isinstance(e, FinalEvent))
    assert final.chunks_used == 0
    assert "没有找到" in final.answer
    assert llm.last_messages == []  # LLM 没被调用


@pytest.mark.asyncio
async def test_stream_answer_includes_history(filled_store):
    llm = FakeLLM(["回答"])
    svc = _make_generation_service(filled_store, llm)

    history = [
        {"role": "user", "content": "之前的问题"},
        {"role": "assistant", "content": "之前的回答"},
    ]
    _ = [ev async for ev in svc.stream_answer("年假？", kb_id=1, history=history)]

    # 验证历史进入了 LLM messages
    msgs = llm.last_messages
    assert msgs[0]["role"] == "system"
    # 中间两条来自 history
    assert {"role": "user", "content": "之前的问题"} in msgs
    assert {"role": "assistant", "content": "之前的回答"} in msgs
    # 最后一条是当前问题
    assert msgs[-1]["role"] == "user"
    assert "年假？" in msgs[-1]["content"]


@pytest.mark.asyncio
async def test_stream_answer_prompt_contains_context(filled_store):
    llm = FakeLLM(["x"])
    svc = _make_generation_service(filled_store, llm)
    _ = [ev async for ev in svc.stream_answer("年假？", kb_id=1)]

    user_prompt = llm.last_messages[-1]["content"]
    assert "员工手册.pdf" in user_prompt
    assert "15 天年休假" in user_prompt
    assert "年假？" in user_prompt
