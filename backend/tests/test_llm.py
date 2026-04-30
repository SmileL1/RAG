"""LLM 适配层测试（mock OpenAI 客户端，不打真实 API）。"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.rag.llm.openai_compatible import OpenAICompatibleLLM


def _make_llm() -> OpenAICompatibleLLM:
    return OpenAICompatibleLLM(
        api_base="http://fake",
        api_key="fake-key",
        model="fake-model",
    )


@pytest.mark.asyncio
async def test_chat_returns_message_content():
    llm = _make_llm()
    fake_resp = MagicMock()
    fake_resp.choices = [MagicMock(message=MagicMock(content="hello"))]
    llm._client.chat.completions.create = AsyncMock(return_value=fake_resp)

    result = await llm.chat([{"role": "user", "content": "hi"}])
    assert result == "hello"


@pytest.mark.asyncio
async def test_stream_chat_yields_tokens():
    llm = _make_llm()

    async def fake_stream():
        for content in ["你", "好", "，", "世", "界"]:
            yield MagicMock(choices=[MagicMock(delta=MagicMock(content=content))])

    llm._client.chat.completions.create = AsyncMock(return_value=fake_stream())

    tokens: list[str] = []
    async for t in llm.stream_chat([{"role": "user", "content": "hi"}]):
        tokens.append(t)
    assert tokens == ["你", "好", "，", "世", "界"]


@pytest.mark.asyncio
async def test_stream_chat_skips_empty_delta():
    llm = _make_llm()

    async def fake_stream():
        # 第一帧 delta 没 content（典型于流首个 chunk 只有 role）
        yield MagicMock(choices=[MagicMock(delta=MagicMock(content=None))])
        yield MagicMock(choices=[MagicMock(delta=MagicMock(content="a"))])
        yield MagicMock(choices=[MagicMock(delta=MagicMock(content=""))])
        yield MagicMock(choices=[MagicMock(delta=MagicMock(content="b"))])

    llm._client.chat.completions.create = AsyncMock(return_value=fake_stream())

    tokens = [t async for t in llm.stream_chat([{"role": "user", "content": "hi"}])]
    assert tokens == ["a", "b"]


def test_requires_api_key():
    with pytest.raises(ValueError, match="API Key"):
        OpenAICompatibleLLM(api_base="x", api_key="", model="m")
