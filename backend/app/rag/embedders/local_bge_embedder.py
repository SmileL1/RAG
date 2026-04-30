"""本地 bge-m3 Embedding（基于 FlagEmbedding）。

- 首次实例化会从 HuggingFace 下载 ~2GB 模型（也可预置到本地路径）
- 支持 CPU 和 GPU；use_fp16=True 在 GPU 上显著加速
- 推理是同步 CPU/GPU 操作，通过 asyncio.to_thread 避免阻塞事件循环
"""
from __future__ import annotations

import asyncio
from typing import Any

from loguru import logger

from app.core.exceptions import EmbeddingError
from app.rag.embedders.base import BaseEmbedder


class LocalBgeEmbedder(BaseEmbedder):
    """本地 BAAI/bge-m3 模型。"""

    def __init__(
        self,
        model_path: str = "BAAI/bge-m3",
        use_fp16: bool = True,
        batch_size: int = 12,
        max_length: int = 8192,
    ):
        self._model_path = model_path
        self._use_fp16 = use_fp16
        self._batch_size = batch_size
        self._max_length = max_length
        self._model: Any | None = None
        self._load_lock = asyncio.Lock()

        self.dimension = 1024
        self.name = "local:bge-m3"

    async def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        async with self._load_lock:
            if self._model is not None:
                return
            logger.info(
                "加载本地 bge-m3 from {}（首次可能需下载 ~2GB）",
                self._model_path,
            )

            def _load() -> Any:
                from FlagEmbedding import BGEM3FlagModel

                return BGEM3FlagModel(self._model_path, use_fp16=self._use_fp16)

            try:
                self._model = await asyncio.to_thread(_load)
            except Exception as e:
                logger.error("bge-m3 加载失败: {}", e)
                raise EmbeddingError(f"本地模型加载失败: {e}") from e
            logger.info("bge-m3 加载完成")

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        await self._ensure_loaded()
        sanitized = [t if t and t.strip() else " " for t in texts]

        def _encode() -> list[list[float]]:
            assert self._model is not None
            output = self._model.encode(
                sanitized,
                batch_size=self._batch_size,
                max_length=self._max_length,
            )
            # FlagEmbedding 返回 dict，"dense_vecs" 是 numpy ndarray
            return output["dense_vecs"].tolist()

        try:
            return await asyncio.to_thread(_encode)
        except Exception as e:
            logger.error("bge-m3 推理失败: {}", e)
            raise EmbeddingError(f"本地嵌入失败: {e}") from e

    async def embed_query(self, query: str) -> list[float]:
        vectors = await self.embed_texts([query])
        return vectors[0]
