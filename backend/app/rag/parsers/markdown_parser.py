"""Markdown 解析器（按 H1/H2 大节切分，保留小节标题）。

只在 H1/H2 处切段——H3~H6 连同正文留在所属大节内，避免把「孤立标题」
切成只有一行的超小段（那种段会成为只含标题的小块，检索时易误命中且无信息量）。
切段后再做兜底：正文为空/极短的「只剩标题」段，并入下一段。
"""
from __future__ import annotations

import asyncio
import re
from pathlib import Path

from loguru import logger

from app.rag.parsers.base import BaseParser, ParsedSegment

# 仅 H1/H2 作为切分点
_H_PATTERN = re.compile(r"^(#{1,2})\s+(.+)$", re.MULTILINE)
# 去掉行首标题后，正文少于这么多字符就视为「只剩标题」，并入下一段
_MIN_BODY_CHARS = 24


def _body_len(section: str, title: str) -> int:
    """估算去掉标题行后的正文长度。"""
    body = section
    first_nl = body.find("\n")
    if first_nl != -1:
        body = body[first_nl + 1 :]
    else:
        body = ""
    return len(body.strip())


class MarkdownParser(BaseParser):
    supported_extensions = {".md", ".markdown"}

    async def parse(self, file_path: Path) -> list[ParsedSegment]:
        def _read() -> list[ParsedSegment]:
            text = file_path.read_text(encoding="utf-8", errors="replace").strip()
            if not text:
                return []

            matches = list(_H_PATTERN.finditer(text))
            if not matches:
                # 没有 H1/H2 标题 → 整文档一段
                return [
                    ParsedSegment(text=text, metadata={"filename": file_path.name})
                ]

            raw: list[ParsedSegment] = []
            # 第一个标题前可能有内容
            if matches[0].start() > 0:
                preface = text[: matches[0].start()].strip()
                if preface:
                    raw.append(
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
                raw.append(
                    ParsedSegment(
                        text=section,
                        metadata={
                            "filename": file_path.name,
                            "section": title,
                            "level": len(m.group(1)),
                        },
                    )
                )

            # 兜底：把「只剩标题」的超小段并入下一段（标题作为下一段开头保留）
            merged: list[ParsedSegment] = []
            carry = ""
            for seg in raw:
                title = str(seg.metadata.get("section", ""))
                if _body_len(seg.text, title) < _MIN_BODY_CHARS:
                    # 正文太短，暂存，拼到下一段前面
                    carry = (carry + "\n\n" + seg.text).strip() if carry else seg.text
                    continue
                if carry:
                    seg = ParsedSegment(
                        text=(carry + "\n\n" + seg.text).strip(),
                        metadata=seg.metadata,
                    )
                    carry = ""
                merged.append(seg)
            # 末尾还残留的 carry（整篇都很碎）作为单独一段，避免丢内容
            if carry:
                if merged:
                    merged[-1] = ParsedSegment(
                        text=(merged[-1].text + "\n\n" + carry).strip(),
                        metadata=merged[-1].metadata,
                    )
                else:
                    merged.append(
                        ParsedSegment(text=carry, metadata={"filename": file_path.name})
                    )
            return merged

        segments = await asyncio.to_thread(_read)
        logger.info("Markdown 解析完成 {}: {} 段", file_path.name, len(segments))
        return segments
