"""FastAPI 应用入口。"""
from __future__ import annotations

import os
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

# 在 asyncio 事件循环启动前、主线程中预先 import FlagEmbedding。
# torch 在非主线程首次 import 时会触发 Windows 线程锁卡死，必须在这里提前完成。
try:
    import FlagEmbedding  # noqa: F401
except Exception:
    pass

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy import select

from app.api import admin, auth, chat, documents, knowledge_base, settings_api
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.exceptions import AppException
from app.core.logging import setup_logging
from app.core.security import hash_password
from app.models.user import User


async def _ensure_admin() -> None:
    """启动时创建默认管理员（幂等）。"""
    logger.info("检查管理员账号……")
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(User).where(User.username == settings.ADMIN_USERNAME)
            )
            existing = result.scalar_one_or_none()
            if existing is not None:
                if not existing.is_admin:
                    existing.is_admin = True
                    await db.commit()
                    logger.info("已补全管理员权限: {}", settings.ADMIN_USERNAME)
                else:
                    logger.info("管理员账号已存在: {}", settings.ADMIN_USERNAME)
                return
            db.add(User(
                username=settings.ADMIN_USERNAME,
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                is_admin=True,
            ))
            await db.commit()
            logger.info("✅ 已创建默认管理员账号: {} / {}", settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD)
        except Exception as e:
            await db.rollback()
            logger.error("❌ 创建默认管理员失败: {}", e)
            raise


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    logger.info(
        "🚀 {app} 启动中… env={env}, embedding={emb}, llm={llm}",
        app=settings.APP_NAME,
        env=settings.APP_ENV,
        emb=settings.EMBEDDING_PROVIDER,
        llm=settings.LLM_PROVIDER,
    )
    _ = settings.upload_dir_path
    _ = settings.qdrant_local_path_resolved
    await _ensure_admin()
    yield
    logger.info("👋 应用关闭")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="RAG 私有知识库系统 · API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    logger.warning("业务异常: {msg}", msg=exc.message)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/", tags=["meta"])
async def root() -> dict:
    return {"name": settings.APP_NAME, "env": settings.APP_ENV, "docs": "/docs"}


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok"}


# 路由注册
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(knowledge_base.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(settings_api.router)
