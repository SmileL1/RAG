"""Word(.docx) 解析器（按标题样式分段，退化为纯文本兜底）。"""
from __future__ import annotations

import asyncio
from pathlib import Path

from docx import Document as DocxDocument
from docx.oxml.ns import qn
from loguru import logger

from app.rag.parsers.base import BaseParser, ParsedSegment

_HEADING_STYLES = {"Heading 1", "Heading 2", "Heading 3",
                   "标题 1", "标题 2", "标题 3",
                   "heading 1", "heading 2", "heading 3"}


def _is_heading(paragraph) -> bool:
    return paragraph.style.name in _HEADING_STYLES or \
           paragraph.style.name.startswith("Heading") or \
           paragraph.style.name.startswith("标题")


def _extract_table_text(table) -> str:
    rows = []
    for row in table.rows:
        cells = [c.text.strip() for c in row.cells if c.text.strip()]
        if cells:
            rows.append(" | ".join(cells))
    return "\n".join(rows)


class DocxParser(BaseParser):
    supported_extensions = {".docx"}

    async def parse(self, file_path: Path) -> list[ParsedSegment]:
        def _read() -> list[ParsedSegment]:
            d = DocxDocument(str(file_path))

            # 按标题样式切段，每个标题开启一个新 segment
            segments: list[ParsedSegment] = []
            current_title: str = "(开头)"
            current_level: int = 0
            current_lines: list[str] = []

            def _flush():
                text = "\n".join(current_lines).strip()
                if text:
                    segments.append(ParsedSegment(
                        text=text,
                        metadata={
                            "filename": file_path.name,
                            "section": current_title,
                            "level": current_level,
                        },
                    ))

            # 遍历文档元素（段落 + 表格，保持原顺序）
            body = d.element.body
            for child in body:
                tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag

                if tag == "p":
                    # 段落
                    from docx.text.paragraph import Paragraph
                    para = Paragraph(child, d)
                    text = (para.text or "").strip()
                    if not text:
                        continue
                    if _is_heading(para):
                        _flush()
                        current_title = text
                        current_level = int(
                            ''.join(filter(str.isdigit, para.style.name)) or "1"
                        )
                        current_lines = [text]
                    else:
                        current_lines.append(text)

                elif tag == "tbl":
                    # 表格
                    from docx.table import Table
                    tbl = Table(child, d)
                    table_text = _extract_table_text(tbl)
                    if table_text:
                        current_lines.append(table_text)

            _flush()

            # 如果文档没有任何标题样式，退化为整文档单段（原来的逻辑）
            if not segments:
                all_text = "\n".join(
                    p.text.strip() for p in d.paragraphs if p.text.strip()
                )
                if all_text:
                    segments = [ParsedSegment(
                        text=all_text,
                        metadata={"filename": file_path.name},
                    )]

            return segments

        segments = await asyncio.to_thread(_read)
        logger.info("DOCX 解析完成 {}: {} 段（按标题分段）", file_path.name, len(segments))
        return segments
