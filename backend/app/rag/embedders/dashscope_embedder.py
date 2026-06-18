"""阿里云 DashScope Embedding（通过 OpenAI 兼容协议）。

Docs: https://help.aliyun.com/zh/dashscope/developer-reference/text-embedding-synchronous-api
- 模型：text-embedding-v3
- 单次最多 10 条文本、单条最长 8192 token（批量上限以服务端为准）
- 维度：默认 1024（也支持 512/768/1536）
"""
from __future__ import annotations

from loguru import logger
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.exceptions import EmbeddingError
from app.rag.embedders.base import BaseEmbedder

DASHSCOPE_COMPAT_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
# DashScope text-embedding 接口单次最多 10 条输入（超过会报 InvalidParameter）
MAX_BATCH = 10


class DashScopeEmbedder(BaseEmbedder):
    """阿里云 DashScope text-embedding-v3。

    通过 OpenAI 兼容接口调用（省掉额外 SDK 依赖、天然 async）。
    """

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-v3",
        dimension: int = 1024,
        base_url: str = DASHSCOPE_COMPAT_BASE,
        timeout: float = 60.0,
    ):
        if not api_key:
            raise ValueError("DASHSCOPE_API_KEY 未配置")
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        self._model = model
        self.dimension = dimension
        self.name = f"dashscope:{model}"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _embed_batch(self, batch: list[str]) -> list[list[float]]:
        try:
            resp = await self._client.embeddings.create(
                model=self._model,
                input=batch,
                dimensions=self.dimension,
                encoding_format="float",
            )
        except Exception as e:
            logger.error("DashScope embedding 请求失败: {}", e)
            raise EmbeddingError(f"DashScope 调用失败: {e}") from e
        return [item.embedding for item in resp.data]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        # DashScope 不接受空字符串，统一替换为单空格占位，避免报错
        sanitized = [t if t and t.strip() else " " for t in texts]

        results: list[list[float]] = []
        for i in range(0, len(sanitized), MAX_BATCH):
            batch = sanitized[i : i + MAX_BATCH]
            logger.debug(
                "DashScope embedding: batch {}/{}, size={}",
                i // MAX_BATCH + 1,
                (len(sanitized) - 1) // MAX_BATCH + 1,
                len(batch),
            )
            vectors = await self._embed_batch(batch)
            results.extend(vectors)
        return results

    async def embed_query(self, query: str) -> list[float]:
        vectors = await self._embed_batch([query or " "])
        return vectors[0]
