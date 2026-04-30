"""LLM 工厂：按配置返回实例（下一轮接入具体实现）。"""
from __future__ import annotations

from app.core.config import settings
from app.rag.llm.base import BaseLLM


def get_llm() -> BaseLLM:
    """所有 OpenAI 兼容协议（DeepSeek/通义/Kimi/OpenAI）共用一个实现。"""
    from app.rag.llm.openai_compatible import OpenAICompatibleLLM

    return OpenAICompatibleLLM(
        api_base=settings.LLM_API_BASE,
        api_key=settings.LLM_API_KEY,
        model=settings.LLM_MODEL,
        default_temperature=settings.LLM_TEMPERATURE,
        default_max_tokens=settings.LLM_MAX_TOKENS,
    )
