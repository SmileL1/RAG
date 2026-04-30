"""Celery 应用实例。"""
from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "rag_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.document_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_track_started=True,
    task_time_limit=30 * 60,  # 单任务最多 30 分钟
    worker_prefetch_multiplier=1,
)
