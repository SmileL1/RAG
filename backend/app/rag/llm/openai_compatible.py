"""OpenAI 兼容协议 LLM 客户端。

DeepSeek / 通义千问 / Kimi / OpenAI / Azure OpenAI 都用这套兼容接口，
只需配置不同的 base_url 与 api_key 即可切换。
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from loguru import logger
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.exceptions import LLMError
from app.rag.llm.base import BaseLLM


class OpenAICompatibleLLM(BaseLLM):
    def __init__(
        self,
        api_base: str,
        api_key: str,
        model: str,
        default_temperature: float = 0.3,
        default_max_tokens: int = 2048,
        timeout: float = 120.0,
    ):
        if not api_key:
            raise ValueError("LLM API Key 未配置")
        self._client = AsyncOpenAI(api_key=api_key, base_url=api_base, timeout=timeout)
        self._model = model
        self._default_temperature = default_temperature
        self._default_max_tokens = default_max_tokens
        self.name = f"openai-compatible:{model}"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        try:
            resp = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature if temperature is not None else self._default_temperature,
                max_tokens=max_tokens or self._default_max_tokens,
                stream=False,
                **kwargs,
            )
        except Exception as e:
            logger.error("LLM chat 失败: {}", e)
            raise LLMError(f"LLM 调用失败: {e}") from e
        return resp.choices[0].message.content or ""

    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """流式 chat。注意这里**不能**叠 tenacity 重试（一旦开始流就不好回放）。"""
        try:
            stream = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature if temperature is not None else self._default_temperature,
                max_tokens=max_tokens or self._default_max_tokens,
                stream=True,
                **kwargs,
            )
        except Exception as e:
            logger.error("LLM stream_chat 启动失败: {}", e)
            raise LLMError(f"LLM 调用失败: {e}") from e

        try:
            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                content = getattr(delta, "content", None)
                if content:
                    yield content
        except Exception as e:
            logger.error("LLM 流式输出中断: {}", e)
            raise LLMError(f"LLM 流式输出中断: {e}") from e
