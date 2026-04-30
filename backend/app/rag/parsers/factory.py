"""Parser 工厂：按扩展名分发。"""
from __future__ import annotations

from app.core.exceptions import UnsupportedFileTypeError
from app.rag.parsers.base import BaseParser
from app.rag.parsers.docx_parser import DocxParser
from app.rag.parsers.html_parser import HtmlParser
from app.rag.parsers.markdown_parser import MarkdownParser
from app.rag.parsers.pdf_parser import PdfParser
from app.rag.parsers.txt_parser import TxtParser

_REGISTRY: list[type[BaseParser]] = [
    PdfParser,
    DocxParser,
    MarkdownParser,
    HtmlParser,
    TxtParser,
]


def get_parser(extension: str) -> BaseParser:
    """根据文件扩展名返回 Parser 实例。"""
    ext = extension.lower()
    if not ext.startswith("."):
        ext = "." + ext
    for cls in _REGISTRY:
        if ext in cls.supported_extensions:
            return cls()
    raise UnsupportedFileTypeError(f"不支持的文件类型: {ext}")


def supported_extensions() -> set[str]:
    out: set[str] = set()
    for cls in _REGISTRY:
        out.update(cls.supported_extensions)
    return out
