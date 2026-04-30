"""冒烟测试：确保 app 能加载、配置能读、根接口可用。"""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "name" in data


@pytest.mark.asyncio
async def test_health_endpoint():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


def test_settings_load():
    from app.core.config import settings

    assert settings.APP_NAME
    assert settings.EMBEDDING_PROVIDER in ("dashscope", "local_bge")
    assert settings.QDRANT_MODE in ("local", "remote")
