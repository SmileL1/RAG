"""运行时配置读写（Admin only）。

可修改的参数在当前进程内立即生效，并写回 .env（重启后依然生效）。
API Key 在读取时遮蔽返回，不回传明文。
"""
from __future__ import annotations

from pathlib import Path

import httpx
from fastapi import APIRouter, Depends
from loguru import logger
from pydantic import BaseModel, Field

from app.api.deps import get_current_admin
from app.core.config import settings

router = APIRouter(
    prefix="/api/settings",
    tags=["settings"],
    dependencies=[Depends(get_current_admin)],
)

# backend/.env（app/api/settings_api.py 向上三级即 backend/）
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"

# 允许写回 .env 的字段
PERSISTABLE = {
    "LLM_PROVIDER",
    "LLM_API_BASE",
    "LLM_MODEL",
    "LLM_API_KEY",
    "LLM_TEMPERATURE",
    "LLM_MAX_TOKENS",
    "RETRIEVE_TOP_K",
    "RERANK_ENABLED",
    "RERANK_TOP_K",
    "USE_HYDE",
}


class SettingsOut(BaseModel):
    # LLM
    LLM_PROVIDER: str
    LLM_API_BASE: str
    LLM_MODEL: str
    LLM_TEMPERATURE: float
    LLM_MAX_TOKENS: int
    # API Key：仅返回是否已设置 + 遮蔽串，不回传明文
    LLM_API_KEY_SET: bool
    LLM_API_KEY_MASKED: str
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
    LLM_PROVIDER: str | None = Field(None, description="LLM 供应商标签")
    LLM_API_BASE: str | None = Field(None, description="LLM API 地址")
    LLM_MODEL: str | None = Field(None, description="模型名称")
    LLM_API_KEY: str | None = Field(None, description="LLM API Key（留空则不修改）")
    LLM_TEMPERATURE: float | None = Field(None, ge=0.0, le=2.0)
    LLM_MAX_TOKENS: int | None = Field(None, ge=256, le=8192)
    RETRIEVE_TOP_K: int | None = Field(None, ge=1, le=50)
    RERANK_ENABLED: bool | None = None
    RERANK_TOP_K: int | None = Field(None, ge=1, le=20)
    USE_HYDE: bool | None = None


class TestLLMOut(BaseModel):
    ok: bool
    message: str
    reply: str | None = None


def _mask(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}****{key[-4:]}"


def _to_out() -> SettingsOut:
    return SettingsOut(
        LLM_PROVIDER=settings.LLM_PROVIDER,
        LLM_API_BASE=settings.LLM_API_BASE,
        LLM_MODEL=settings.LLM_MODEL,
        LLM_TEMPERATURE=settings.LLM_TEMPERATURE,
        LLM_MAX_TOKENS=settings.LLM_MAX_TOKENS,
        LLM_API_KEY_SET=bool(settings.LLM_API_KEY),
        LLM_API_KEY_MASKED=_mask(settings.LLM_API_KEY),
        EMBEDDING_PROVIDER=settings.EMBEDDING_PROVIDER,
        RETRIEVE_TOP_K=settings.RETRIEVE_TOP_K,
        RERANK_ENABLED=settings.RERANK_ENABLED,
        RERANK_TOP_K=settings.RERANK_TOP_K,
        USE_HYDE=settings.USE_HYDE,
        QDRANT_MODE=settings.QDRANT_MODE,
        INGEST_MODE=settings.INGEST_MODE,
    )


def _fmt_env(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _persist_env(changes: dict) -> None:
    """把变更写回 .env：命中的 key 原地替换，未出现的追加到末尾，保留注释与顺序。"""
    to_write = {k: v for k, v in changes.items() if k in PERSISTABLE}
    if not to_write or not ENV_PATH.exists():
        return

    lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in line:
            key = line.split("=", 1)[0].strip()
            if key in to_write:
                out.append(f"{key}={_fmt_env(to_write[key])}")
                seen.add(key)
                continue
        out.append(line)

    for key, value in to_write.items():
        if key not in seen:
            out.append(f"{key}={_fmt_env(value)}")

    ENV_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")


def _is_local_llm(base: str) -> bool:
    b = (base or "").lower()
    return "11434" in b or "ollama" in b


def _ollama_root(base: str) -> str:
    """从 OpenAI 兼容 base（.../v1）推导 Ollama 原生根地址。"""
    b = (base or "").strip().rstrip("/")
    if b.endswith("/v1"):
        b = b[:-3]
    return b or "http://127.0.0.1:11434"


class OllamaModelsOut(BaseModel):
    ok: bool
    models: list[str]
    message: str = ""


@router.get("", response_model=SettingsOut)
async def get_settings():
    return _to_out()


@router.get("/ollama-models", response_model=OllamaModelsOut)
async def ollama_models(base: str | None = None):
    """列出本机 Ollama 已安装的模型（调用 Ollama 原生 /api/tags）。"""
    root = _ollama_root(base or settings.LLM_API_BASE)
    if not _is_local_llm(root):
        root = "http://127.0.0.1:11434"
    url = root.rstrip("/") + "/api/tags"
    try:
        async with httpx.AsyncClient(timeout=4.0, trust_env=False) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
        models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
        if not models:
            return OllamaModelsOut(
                ok=True, models=[], message="Ollama 已连接，但未安装模型（先执行 ollama pull <模型>）"
            )
        return OllamaModelsOut(ok=True, models=models)
    except Exception as e:
        return OllamaModelsOut(ok=False, models=[], message=f"未能连接本地 Ollama（{url}）：{e}")


@router.patch("", response_model=SettingsOut)
async def patch_settings(body: SettingsPatch):
    changes = body.model_dump(exclude_none=True)
    # API Key 若传空白串视为不修改
    if "LLM_API_KEY" in changes and not str(changes["LLM_API_KEY"]).strip():
        changes.pop("LLM_API_KEY")
    else:
        if "LLM_API_KEY" in changes:
            changes["LLM_API_KEY"] = str(changes["LLM_API_KEY"]).strip()

    for field, value in changes.items():
        object.__setattr__(settings, field, value)

    # Ollama / 本地端点不需要真实 Key，但 OpenAI 客户端要求非空，自动补占位
    if _is_local_llm(settings.LLM_API_BASE) and not (settings.LLM_API_KEY or "").strip():
        object.__setattr__(settings, "LLM_API_KEY", "ollama")
        changes["LLM_API_KEY"] = "ollama"

    if changes:
        try:
            _persist_env(changes)
        except Exception as e:  # 持久化失败不影响运行时已生效
            logger.warning("写回 .env 失败（运行时已生效）: {}", e)

    return _to_out()


@router.post("/test-llm", response_model=TestLLMOut)
async def test_llm():
    """用当前生效的 LLM 配置发一次最小调用，验证 Key/地址/模型是否连通。"""
    from app.rag.llm.factory import get_llm

    try:
        llm = get_llm()
        reply = await llm.chat(
            [{"role": "user", "content": "回复「连接成功」四个字即可"}],
            max_tokens=20,
        )
        return TestLLMOut(ok=True, message="连接成功", reply=(reply or "").strip()[:60])
    except Exception as e:
        return TestLLMOut(ok=False, message=str(e))
