"""HTML 解析器（基于 BeautifulSoup + lxml）。"""
from __future__ import annotations

import asyncio
from pathlib import Path

from bs4 import BeautifulSoup
from loguru import logger

from app.rag.parsers.base import BaseParser, ParsedSegment


class HtmlParser(BaseParser):
    supported_extensions = {".html", ".htm"}

    async def parse(self, file_path: Path) -> list[ParsedSegment]:
        def _read() -> list[ParsedSegment]:
            html = file_path.read_text(encoding="utf-8", errors="replace")
            soup = BeautifulSoup(html, "lxml")

            # 去除脚本/样式/导航/页脚等噪声
            for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
                tag.decompose()

            text = soup.get_text(separator="\n").strip()
            text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
            if not text:
                return []

            title = soup.title.string.strip() if soup.title and soup.title.string else file_path.name
            return [
                ParsedSegment(
                    text=text,
                    metadata={"filename": file_path.name, "title": title},
                )
            ]

        segments = await asyncio.to_thread(_read)
        logger.info("HTML 解析完成 {}: {} 段", file_path.name, len(segments))
        return segments
