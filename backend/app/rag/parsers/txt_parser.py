"""纯文本解析器。"""
from __future__ import annotations

import asyncio
from pathlib import Path

from loguru import logger

from app.rag.parsers.base import BaseParser, ParsedSegment


class TxtParser(BaseParser):
    supported_extensions = {".txt"}

    async def parse(self, file_path: Path) -> list[ParsedSegment]:
        def _read() -> list[ParsedSegment]:
            text = file_path.read_text(encoding="utf-8", errors="replace").strip()
            if not text:
                return []
            return [
                ParsedSegment(
                    text=text,
                    metadata={"filename": file_path.name},
                )
            ]

        segments = await asyncio.to_thread(_read)
        logger.info("TXT 解析完成 {}: {} 段", file_path.name, len(segments))
        return segments
