"""Embedder 工厂：按配置返回单例实例。

bge-m3 模型加载昂贵，必须缓存单例；DashScope 客户端也没必要重复创建。
切换配置 / 测试时使用 reset_embedder() 清除缓存。
"""
from __future__ import annotations

from app.core.config import settings
from app.rag.embedders.base import BaseEmbedder

_embedder: BaseEmbedder | None = None


def get_embedder() -> BaseEmbedder:
    global _embedder
    if _embedder is not None:
        return _embedder

    provider = settings.EMBEDDING_PROVIDER
    if provider == "dashscope":
        from app.rag.embedders.dashscope_embedder import DashScopeEmbedder

        _embedder = DashScopeEmbedder(
            api_key=settings.DASHSCOPE_API_KEY,
            model=settings.DASHSCOPE_EMBEDDING_MODEL,
        )
    elif provider == "local_bge":
        from app.rag.embedders.local_bge_embedder import LocalBgeEmbedder

        _embedder = LocalBgeEmbedder(model_path=settings.LOCAL_BGE_MODEL_PATH)
    else:
        raise ValueError(f"未知 EMBEDDING_PROVIDER: {provider}")

    return _embedder


def reset_embedder() -> None:
    """清除单例（测试或切换配置时用）。"""
    global _embedder
    _embedder = None
