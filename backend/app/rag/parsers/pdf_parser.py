"""PDF 解析器（基于 pypdf，按页输出 ParsedSegment）。"""
from __future__ import annotations

import asyncio
from pathlib import Path

from loguru import logger
from pypdf import PdfReader

from app.rag.parsers.base import BaseParser, ParsedSegment


class PdfParser(BaseParser):
    supported_extensions = {".pdf"}

    async def parse(self, file_path: Path) -> list[ParsedSegment]:
        def _read() -> list[ParsedSegment]:
            reader = PdfReader(str(file_path))
            segments: list[ParsedSegment] = []
            for page_num, page in enumerate(reader.pages, start=1):
                try:
                    text = page.extract_text() or ""
                except Exception as e:  # 个别页解析失败不影响整体
                    logger.warning("PDF 第 {} 页解析失败: {}", page_num, e)
                    continue
                text = text.strip()
                if not text:
                    continue
                segments.append(
                    ParsedSegment(
                        text=text,
                        metadata={
                            "filename": file_path.name,
                            "page": page_num,
                            "total_pages": len(reader.pages),
                        },
                    )
                )
            return segments

        segments = await asyncio.to_thread(_read)
        logger.info("PDF 解析完成 {}: {} 段", file_path.name, len(segments))
        return segments
