"""运行时配置读写（Admin only）。

可修改的参数在当前进程内立即生效，重启后恢复 .env 的值。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import get_current_admin
from app.core.config import settings

router = APIRouter(
    prefix="/api/settings",
    tags=["settings"],
    dependencies=[Depends(get_current_admin)],
)


class SettingsOut(BaseModel):
    # LLM
    LLM_PROVIDER: str
    LLM_API_BASE: str
    LLM_MODEL: str
    LLM_TEMPERATURE: float
    LLM_MAX_TOKENS: int
    # Embedding（只读，切换需重建知识库）
    EMBEDDING_PROVIDER: str
    # Retrieval
    RETRIEVE_TOP_K: int
    RERANK_ENABLED: bool
    RERANK_TOP_K: int
    USE_HYDE: bool
    # Qdrant（只读，供展示）
    QDRANT_MODE: str
    INGEST_MODE: str


class SettingsPatch(BaseModel):
    LLM_API_BASE: str | None = Field(None, description="LLM API 地址")
    LLM_MODEL: str | None = Field(None, description="模型名称")
    LLM_TEMPERATURE: float | None = Field(None, ge=0.0, le=2.0)
    LLM_MAX_TOKENS: int | None = Field(None, ge=256, le=8192)
    RETRIEVE_TOP_K: int | None = Field(None, ge=1, le=50)
    RERANK_ENABLED: bool | None = None
    RERANK_TOP_K: int | None = Field(None, ge=1, le=20)
    USE_HYDE: bool | None = None


def _to_out() -> SettingsOut:
    return SettingsOut(
        LLM_PROVIDER=settings.LLM_PROVIDER,
        LLM_API_BASE=settings.LLM_API_BASE,
        LLM_MODEL=settings.LLM_MODEL,
        LLM_TEMPERATURE=settings.LLM_TEMPERATURE,
        LLM_MAX_TOKENS=settings.LLM_MAX_TOKENS,
        EMBEDDING_PROVIDER=settings.EMBEDDING_PROVIDER,
        RETRIEVE_TOP_K=settings.RETRIEVE_TOP_K,
        RERANK_ENABLED=settings.RERANK_ENABLED,
        RERANK_TOP_K=settings.RERANK_TOP_K,
        USE_HYDE=settings.USE_HYDE,
        QDRANT_MODE=settings.QDRANT_MODE,
        INGEST_MODE=settings.INGEST_MODE,
    )


@router.get("", response_model=SettingsOut)
async def get_settings():
    return _to_out()


@router.patch("", response_model=SettingsOut)
async def patch_settings(body: SettingsPatch):
    for field, value in body.model_dump(exclude_none=True).items():
        object.__setattr__(settings, field, value)
    return _to_out()
