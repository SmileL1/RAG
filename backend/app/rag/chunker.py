"""文档分块。

基于 LlamaIndex 的 SentenceSplitter，针对中文做了分隔符调整：
  - 段落分隔：\\n\\n
  - 二级分块：按中英文标点（,.;。？！；，）切句
分块后保留原 segment 的 metadata（filename / page / section 等），
并补 chunk_idx（全局）和 sub_chunk_idx（同 segment 内）。
"""
from __future__ import annotations

from typing import Any

from llama_index.core.node_parser import SentenceSplitter
from loguru import logger
from pydantic import BaseModel, Field

from app.rag.parsers.base import ParsedSegment

# 中英文标点；末尾问号叹号也是 sentence 终止符
_CN_REGEX = r"[^,.;。？！；，]+[,.;。？！；，]?"


class ChunkData(BaseModel):
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class Chunker:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self._splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            paragraph_separator="\n\n",
            secondary_chunking_regex=_CN_REGEX,
        )
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def chunk(self, segments: list[ParsedSegment]) -> list[ChunkData]:
        result: list[ChunkData] = []
        global_idx = 0
        for seg in segments:
            text = seg.text.strip()
            if not text:
                continue
            try:
                pieces = self._splitter.split_text(text)
            except Exception as e:
                logger.warning("Chunker 分块失败，回退为单块: {}", e)
                pieces = [text]
            for sub_idx, piece in enumerate(pieces):
                p = (piece or "").strip()
                if not p:
                    continue
                meta = dict(seg.metadata)
                meta["chunk_idx"] = global_idx
                meta["sub_chunk_idx"] = sub_idx
                result.append(ChunkData(text=p, metadata=meta))
                global_idx += 1
        logger.debug(
            "Chunker: {} segments → {} chunks (size={}, overlap={})",
            len(segments),
            len(result),
            self._chunk_size,
            self._chunk_overlap,
        )
        return result
