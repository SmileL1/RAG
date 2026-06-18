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

# 小于这么多字符的块视为「碎块」，合并到相邻块（适用于所有格式：标题行、残句等）
_MIN_CHUNK_CHARS = 60


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
                meta["sub_chunk_idx"] = sub_idx
                result.append(ChunkData(text=p, metadata=meta))

        # 合并碎块：把过短的块并入相邻块（默认并入上一块；首块并入下一块）
        result = self._merge_small(result)

        # 重新编全局 chunk_idx
        for i, c in enumerate(result):
            c.metadata["chunk_idx"] = i

        logger.debug(
            "Chunker: {} segments → {} chunks (size={}, overlap={})",
            len(segments),
            len(result),
            self._chunk_size,
            self._chunk_overlap,
        )
        return result

    @staticmethod
    def _merge_small(chunks: list[ChunkData]) -> list[ChunkData]:
        if not chunks:
            return chunks
        merged: list[ChunkData] = []
        carry: ChunkData | None = None  # 暂存：还没有可并入的「上一块」时的碎块
        for c in chunks:
            small = len(c.text) < _MIN_CHUNK_CHARS
            if small and merged:
                # 并入上一块
                prev = merged[-1]
                prev.text = (prev.text + "\n" + c.text).strip()
                continue
            if small and not merged:
                # 还没有上一块，先攒着，拼到下一块前面
                if carry is None:
                    carry = ChunkData(text=c.text, metadata=dict(c.metadata))
                else:
                    carry.text = (carry.text + "\n" + c.text).strip()
                continue
            if carry is not None:
                c = ChunkData(text=(carry.text + "\n" + c.text).strip(), metadata=dict(c.metadata))
                carry = None
            merged.append(c)
        # 整批都很碎，只剩 carry
        if carry is not None:
            if merged:
                merged[-1].text = (merged[-1].text + "\n" + carry.text).strip()
            else:
                merged.append(carry)
        return merged
