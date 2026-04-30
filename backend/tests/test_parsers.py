"""Parser 测试（聚焦于 TXT / Markdown / Factory；PDF/DOCX/HTML 留集成测试）。"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.core.exceptions import UnsupportedFileTypeError
from app.rag.parsers.factory import get_parser, supported_extensions


@pytest.mark.asyncio
async def test_txt_parser(tmp_path: Path):
    f = tmp_path / "demo.txt"
    f.write_text("hello world\n第二行 中文", encoding="utf-8")

    parser = get_parser(".txt")
    segs = await parser.parse(f)

    assert len(segs) == 1
    assert "hello" in segs[0].text
    assert "中文" in segs[0].text
    assert segs[0].metadata["filename"] == "demo.txt"


@pytest.mark.asyncio
async def test_txt_parser_empty_file(tmp_path: Path):
    f = tmp_path / "empty.txt"
    f.write_text("   \n  ", encoding="utf-8")
    parser = get_parser(".txt")
    segs = await parser.parse(f)
    assert segs == []


@pytest.mark.asyncio
async def test_markdown_parser_with_headings(tmp_path: Path):
    md = """# 标题一

这是介绍段落。

## 子标题 A

A 节内容。
有多行。

## 子标题 B

B 节内容。
"""
    f = tmp_path / "doc.md"
    f.write_text(md, encoding="utf-8")
    parser = get_parser(".md")
    segs = await parser.parse(f)

    # 1 个 H1 + 2 个 H2 = 3 段
    assert len(segs) == 3
    assert segs[0].metadata["section"] == "标题一"
    assert segs[1].metadata["section"] == "子标题 A"
    assert segs[2].metadata["section"] == "子标题 B"
    assert segs[1].metadata["level"] == 2


@pytest.mark.asyncio
async def test_markdown_parser_no_headings(tmp_path: Path):
    f = tmp_path / "plain.md"
    f.write_text("无标题的纯内容", encoding="utf-8")
    parser = get_parser(".md")
    segs = await parser.parse(f)
    assert len(segs) == 1
    assert segs[0].text == "无标题的纯内容"


def test_factory_dispatch_known_extensions():
    assert get_parser(".txt").__class__.__name__ == "TxtParser"
    assert get_parser(".md").__class__.__name__ == "MarkdownParser"
    assert get_parser(".markdown").__class__.__name__ == "MarkdownParser"
    assert get_parser(".pdf").__class__.__name__ == "PdfParser"
    assert get_parser(".docx").__class__.__name__ == "DocxParser"
    assert get_parser(".html").__class__.__name__ == "HtmlParser"
    assert get_parser(".htm").__class__.__name__ == "HtmlParser"


def test_factory_normalizes_extension():
    # 不带点也能识别
    assert get_parser("txt").__class__.__name__ == "TxtParser"
    # 大小写无关
    assert get_parser(".TXT").__class__.__name__ == "TxtParser"


def test_factory_unknown_extension():
    with pytest.raises(UnsupportedFileTypeError):
        get_parser(".xyz")


def test_supported_extensions_contains_all():
    exts = supported_extensions()
    assert {".pdf", ".docx", ".md", ".markdown", ".html", ".htm", ".txt"}.issubset(exts)
