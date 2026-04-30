"""Embedding 抽象基类。"""
from __future__ import annotations

from abc import ABC, abstractmethod


class BaseEmbedder(ABC):
    """Embedding 提供方需实现的统一接口。"""

    name: str
    dimension: int

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """批量文本 → 向量。用于建库（document embedding）。"""

    @abstractmethod
    async def embed_query(self, query: str) -> list[float]:
        """单个查询 → 向量。某些模型 query/document 有前缀差异。"""
