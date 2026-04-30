"""应用配置：从 .env 读取，全字段类型化。"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ===== 应用 =====
    APP_NAME: str = "RAG Assistant"
    APP_ENV: str = "dev"
    DEBUG: bool = True
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # ===== 数据库 =====
    DATABASE_URL: str = "postgresql+asyncpg://rag_user:rag_pass@localhost:5432/rag_db"

    # ===== Redis / Celery =====
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ===== Qdrant =====
    QDRANT_MODE: str = "local"  # local | remote
    QDRANT_LOCAL_PATH: str = "./data/qdrant"
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str = ""

    # ===== Embedding 双通道 =====
    EMBEDDING_PROVIDER: str = "dashscope"  # dashscope | local_bge
    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_EMBEDDING_MODEL: str = "text-embedding-v3"
    LOCAL_BGE_MODEL_PATH: str = "BAAI/bge-m3"

    # ===== LLM =====
    LLM_PROVIDER: str = "deepseek"
    LLM_API_BASE: str = "https://api.deepseek.com/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "deepseek-chat"
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 2048

    # ===== Reranker =====
    RERANK_ENABLED: bool = True
    RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"
    RERANK_TOP_K: int = 5

    # ===== Retrieval =====
    RETRIEVE_TOP_K: int = 20
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    USE_HYDE: bool = False

    # ===== 上传 =====
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 100
    ALLOWED_EXTENSIONS: str = ".pdf,.docx,.md,.txt,.html"

    # ===== 入库模式 =====
    # sync   = API 进程内 BackgroundTasks 异步处理（无需 Celery，本地开发用）
    # celery = 提交到 Celery Worker（生产用，要求 Qdrant remote 模式避免本地文件锁冲突）
    INGEST_MODE: str = "sync"

    # ===== JWT / 认证 =====
    JWT_SECRET: str = "change-me-in-production"
    JWT_EXPIRE_DAYS: int = 7
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"

    # ===== 企业微信（v2）=====
    WECOM_ENABLED: bool = False
    WECOM_BOT_ID: str = ""
    WECOM_BOT_SECRET: str = ""
    WECOM_DEFAULT_KB_ID: int | None = None

    # ----- 派生属性 -----
    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_extension_set(self) -> set[str]:
        return {e.strip().lower() for e in self.ALLOWED_EXTENSIONS.split(",") if e.strip()}

    @property
    def upload_dir_path(self) -> Path:
        p = Path(self.UPLOAD_DIR).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def qdrant_local_path_resolved(self) -> Path:
        p = Path(self.QDRANT_LOCAL_PATH).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @field_validator("WECOM_DEFAULT_KB_ID", mode="before")
    @classmethod
    def _coerce_wecom_kb_id(cls, v: object) -> int | None:
        if v == "" or v is None:
            return None
        return int(str(v))

    @field_validator("EMBEDDING_PROVIDER")
    @classmethod
    def _check_embedding_provider(cls, v: str) -> str:
        if v not in {"dashscope", "local_bge"}:
            raise ValueError(f"EMBEDDING_PROVIDER must be 'dashscope' or 'local_bge', got '{v}'")
        return v

    @field_validator("QDRANT_MODE")
    @classmethod
    def _check_qdrant_mode(cls, v: str) -> str:
        if v not in {"local", "remote"}:
            raise ValueError(f"QDRANT_MODE must be 'local' or 'remote', got '{v}'")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
