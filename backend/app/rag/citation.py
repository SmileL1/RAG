"""从检索结果提取溯源引用。"""
from __future__ import annotations

from app.rag.vector_store import SearchResult
from app.schemas.chat import Citation


def extract_citations(results: list[SearchResult]) -> list[Citation]:
    citations: list[Citation] = []
    for r in results:
        meta = r.metadata or {}
        citations.append(
            Citation(
                doc_id=r.doc_id,
                filename=meta.get("filename", "未知文件"),
                page=meta.get("page"),
                chunk_idx=r.chunk_idx,
                text=r.text,
                score=r.score,
            )
        )
    return citations
