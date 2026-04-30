"""Markdown 解析器（按 H1/H2 大节切分，保留小节标题）。"""
from __future__ import annotations

import asyncio
import re
from pathlib import Path

from loguru import logger

from app.rag.parsers.base import BaseParser, ParsedSegment

_H_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


class MarkdownParser(BaseParser):
    supported_extensions = {".md", ".markdown"}

    async def parse(self, file_path: Path) -> list[ParsedSegment]:
        def _read() -> list[ParsedSegment]:
            text = file_path.read_text(encoding="utf-8", errors="replace").strip()
            if not text:
                return []

            # 找出所有标题位置
            matches = list(_H_PATTERN.finditer(text))
            if not matches:
                # 没有标题 → 整文档一段
                return [
                    ParsedSegment(text=text, metadata={"filename": file_path.name})
                ]

            segments: list[ParsedSegment] = []
            # 第一个标题前可能有内容
            if matches[0].start() > 0:
                preface = text[: matches[0].start()].strip()
                if preface:
                    segments.append(
                        ParsedSegment(
                            text=preface,
                            metadata={"filename": file_path.name, "section": "(preface)"},
                        )
                    )

            for i, m in enumerate(matches):
                start = m.start()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                section = text[start:end].strip()
                if not section:
                    continue
                title = m.group(2).strip()
                segments.append(
                    ParsedSegment(
                        text=section,
                        metadata={
                            "filename": file_path.name,
                            "section": title,
                            "level": len(m.group(1)),
                        },
                    )
                )
            return segments

        segments = await asyncio.to_thread(_read)
        logger.info("Markdown 解析完成 {}: {} 段", file_path.name, len(segments))
        return segments
