"""Embedder 测试：mock 外部调用，不真实打 API/加载模型。

真实 API 测试属于集成测试范畴，需额外配置 API Key，由专门的 e2e 流程跑。
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.mark.asyncio
async def test_dashscope_embed_texts_batches_and_returns_vectors():
    from app.rag.embedders.dashscope_embedder import DashScopeEmbedder

    embedder = DashScopeEmbedder(api_key="fake-key")
    # 构造 30 条输入，强制跨两个 batch（每批 25）
    inputs = [f"text-{i}" for i in range(30)]

    fake_resp_1 = MagicMock()
    fake_resp_1.data = [MagicMock(embedding=[0.1] * 1024) for _ in range(25)]
    fake_resp_2 = MagicMock()
    fake_resp_2.data = [MagicMock(embedding=[0.2] * 1024) for _ in range(5)]

    embedder._client.embeddings.create = AsyncMock(side_effect=[fake_resp_1, fake_resp_2])

    vectors = await embedder.embed_texts(inputs)

    assert len(vectors) == 30
    assert all(len(v) == 1024 for v in vectors)
    # 前 25 条用 resp_1，后 5 条用 resp_2
    assert vectors[0][0] == 0.1
    assert vectors[25][0] == 0.2
    assert embedder._client.embeddings.create.await_count == 2


@pytest.mark.asyncio
async def test_dashscope_embed_query():
    from app.rag.embedders.dashscope_embedder import DashScopeEmbedder

    embedder = DashScopeEmbedder(api_key="fake-key")
    fake_resp = MagicMock()
    fake_resp.data = [MagicMock(embedding=[0.5] * 1024)]
    embedder._client.embeddings.create = AsyncMock(return_value=fake_resp)

    v = await embedder.embed_query("hello")
    assert len(v) == 1024
    assert v[0] == 0.5


@pytest.mark.asyncio
async def test_dashscope_empty_input_returns_empty():
    from app.rag.embedders.dashscope_embedder import DashScopeEmbedder

    embedder = DashScopeEmbedder(api_key="fake-key")
    # 也不应调用 API
    mock_create = AsyncMock()
    embedder._client.embeddings.create = mock_create

    result = await embedder.embed_texts([])
    assert result == []
    mock_create.assert_not_awaited()


@pytest.mark.asyncio
async def test_dashscope_sanitizes_empty_strings():
    """空字符串会被替换为单空格，避免 API 拒绝。"""
    from app.rag.embedders.dashscope_embedder import DashScopeEmbedder

    embedder = DashScopeEmbedder(api_key="fake-key")
    fake_resp = MagicMock()
    fake_resp.data = [MagicMock(embedding=[0.0] * 1024) for _ in range(3)]
    mock_create = AsyncMock(return_value=fake_resp)
    embedder._client.embeddings.create = mock_create

    await embedder.embed_texts(["", "   ", "valid"])

    call_args = mock_create.await_args
    inputs_sent = call_args.kwargs["input"]
    assert all(s.strip() or s == " " for s in inputs_sent)


def test_dashscope_requires_api_key():
    from app.rag.embedders.dashscope_embedder import DashScopeEmbedder

    with pytest.raises(ValueError, match="DASHSCOPE_API_KEY"):
        DashScopeEmbedder(api_key="")


def test_factory_caches_singleton(monkeypatch):
    from app.core.config import settings
    from app.rag.embedders.factory import get_embedder, reset_embedder

    reset_embedder()
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "dashscope")
    monkeypatch.setattr(settings, "DASHSCOPE_API_KEY", "fake-key")

    e1 = get_embedder()
    e2 = get_embedder()
    assert e1 is e2

    reset_embedder()
    e3 = get_embedder()
    assert e3 is not e1


def test_factory_rejects_unknown_provider(monkeypatch):
    from app.core.config import settings
    from app.rag.embedders.factory import get_embedder, reset_embedder

    reset_embedder()
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "invalid_provider_xxx")
    with pytest.raises(ValueError, match="未知"):
        get_embedder()
    reset_embedder()


@pytest.mark.asyncio
async def test_local_bge_lazy_loads_model(monkeypatch):
    """确认 bge-m3 懒加载：构造时不加载，首次 embed 才加载。"""
    from app.rag.embedders.local_bge_embedder import LocalBgeEmbedder

    embedder = LocalBgeEmbedder(model_path="fake/path")
    assert embedder._model is None

    # mock 掉 _ensure_loaded 和 _encode 避免真的下载模型
    fake_model = MagicMock()
    fake_model.encode.return_value = {
        "dense_vecs": _FakeNdArray([[0.3] * 1024, [0.4] * 1024])
    }
    embedder._model = fake_model

    vectors = await embedder.embed_texts(["a", "b"])
    assert len(vectors) == 2
    assert vectors[0][0] == 0.3
    fake_model.encode.assert_called_once()


class _FakeNdArray:
    """模拟 numpy ndarray 的 .tolist() 行为。"""

    def __init__(self, data):
        self._data = data

    def tolist(self):
        return self._data
