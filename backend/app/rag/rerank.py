"""Reranker（重排器）：把召回的 Top-N 用更精准的模型重新打分。

为什么需要 Rerank？
  Embedding 检索快但精度有上限（双塔模型，query/doc 各编码一次）。
  Reranker 是 cross-encoder：把 query 和 doc 拼一起送进模型，更准确判断相关度。
  典型套路：粗筛 Top-20（向量） → 精排 Top-5（reranker）→ 喂 LLM。
  这一步通常能让 RAG 准确率提升 15~30%。

模型：BAAI/bge-reranker-v2-m3（约 568MB，CPU 也能跑，GPU 飞快）
"""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any

from loguru import logger

from app.core.config import settings
from app.core.exceptions import AppException
from app.rag.vector_store import SearchResult


class BaseReranker(ABC):
    name: str

    @abstractmethod
    async def rerank(
        self,
        query: str,
        candidates: list[SearchResult],
        top_k: int,
    ) -> list[SearchResult]:
        """对候选段落重新打分，返回按新分数排序的前 top_k 个。"""


class LocalBgeReranker(BaseReranker):
    """本地 bge-reranker-v2-m3。"""

    def __init__(
        self,
        model_path: str = "BAAI/bge-reranker-v2-m3",
        use_fp16: bool = False,
        batch_size: int = 16,
        normalize: bool = True,
    ):
        self._model_path = model_path
        self._use_fp16 = use_fp16
        self._batch_size = batch_size
        self._normalize = normalize
        self._model: Any | None = None
        self._load_lock = asyncio.Lock()
        self.name = f"local:{model_path.split('/')[-1]}"

    async def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        async with self._load_lock:
            if self._model is not None:
                return

            def _load() -> Any:
                import os
                import threading
                import time
                from pathlib import Path as _Path

                _MIRROR = "https://hf-mirror.com"
                os.environ["HF_ENDPOINT"] = _MIRROR

                # 本地模型存放目录（固定路径，避免依赖 HF 缓存结构）
                local_dir = _Path.home() / ".cache" / "rag_models" / self._model_path.split("/")[-1]
                model_file = local_dir / "model.safetensors"

                # 心跳线程
                _stop = threading.Event()
                def _heartbeat(phase: str) -> None:
                    waited = 0
                    while not _stop.wait(30):
                        waited += 30
                        logger.info("Reranker {}中，已等待 {}s……", phase, waited)

                # ── 第一步：下载（如果本地没有）──
                if not model_file.exists():
                    logger.info("Reranker：本地无模型，开始从 {} 下载到 {}……", _MIRROR, local_dir)
                    _stop.clear()
                    threading.Thread(target=_heartbeat, args=("下载",), daemon=True).start()
                    try:
                        from huggingface_hub import snapshot_download
                        snapshot_download(
                            repo_id=self._model_path,
                            local_dir=str(local_dir),
                            endpoint=_MIRROR,
                            ignore_patterns=["*.png", "*.jpg", "assets/*", "README.md", ".gitattributes"],
                        )
                        logger.info("Reranker：下载完成，保存至 {}", local_dir)
                    except Exception as e:
                        raise RuntimeError(f"模型下载失败: {e}") from e
                    finally:
                        _stop.set()
                else:
                    logger.info("Reranker：模型已在本地 {}，跳过下载", local_dir)

                # ── 第二步：加载（从本地目录，不走网络）──
                logger.info("Reranker：开始加载模型（文件约 2GB，需 1~3 分钟）……")
                _stop.clear()
                threading.Thread(target=_heartbeat, args=("加载",), daemon=True).start()
                try:
                    start = time.time()
                    from FlagEmbedding import FlagReranker
                    model = FlagReranker(str(local_dir), use_fp16=self._use_fp16)
                    elapsed = time.time() - start
                    logger.info("Reranker 加载完成，耗时 {:.1f}s", elapsed)
                except Exception:
                    _stop.set()
                    raise
                _stop.set()

                # 预热：触发 PyTorch JIT 编译，避免首次真实推理卡顿
                try:
                    model.compute_score([["warmup", "warmup"]], max_length=64, normalize=False)
                    logger.info("Reranker 预热完成")
                except Exception as e:
                    logger.warning("Reranker 预热失败（不影响正常使用）: {}", e)
                return model

            try:
                self._model = await asyncio.to_thread(_load)
            except Exception as e:
                logger.error("Reranker 加载失败: {}", e)
                raise AppException(f"Reranker 加载失败: {e}") from e

    async def rerank(
        self,
        query: str,
        candidates: list[SearchResult],
        top_k: int,
    ) -> list[SearchResult]:
        if not candidates:
            return []
        if len(candidates) <= top_k and len(candidates) <= 1:
            # 1 条无需重排
            return candidates[:top_k]

        await self._ensure_loaded()
        pairs = [[query, c.text] for c in candidates]

        def _score() -> list[float]:
            assert self._model is not None
            scores = self._model.compute_score(
                pairs,
                batch_size=self._batch_size,
                max_length=256,   # 默认 512，减半显著降低推理时间
                normalize=self._normalize,
            )
            # FlagReranker 单 pair 时返回 float，多 pair 时返回 list[float]
            if isinstance(scores, (int, float)):
                result = [float(scores)]
            else:
                result = [float(s) for s in scores]
            logger.info(
                "Reranker 打分完成 (normalize={}) 前5项: {}",
                self._normalize,
                [round(s, 4) for s in result[:5]],
            )
            return result

        try:
            scores = await asyncio.to_thread(_score)
        except Exception as e:
            logger.error("Reranker 推理失败，降级返回原始候选: {}", e)
            return candidates[:top_k]

        # 按新分数排序
        scored = list(zip(candidates, scores, strict=True))
        scored.sort(key=lambda x: x[1], reverse=True)

        # 把 reranker 分数覆盖到 score 字段（便于上层展示用）
        result: list[SearchResult] = []
        for cand, new_score in scored[:top_k]:
            new_cand = cand.model_copy(update={"score": new_score})
            result.append(new_cand)
        return result


# ===== 工厂（单例）=====

_reranker: BaseReranker | None = None


def get_reranker() -> BaseReranker | None:
    """返回 reranker 实例；若未启用则返回 None。"""
    global _reranker
    if not settings.RERANK_ENABLED:
        return None
    if _reranker is not None:
        return _reranker
    _reranker = LocalBgeReranker(model_path=settings.RERANKER_MODEL)
    return _reranker


def reset_reranker() -> None:
    global _reranker
    _reranker = None
