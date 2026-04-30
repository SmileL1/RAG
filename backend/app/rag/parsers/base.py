"""文档解析器抽象基类。"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class ParsedSegment(BaseModel):
    """解析得到的一段文本，附带元数据（页码、章节等）。"""

    text: str
    metadata: dict[str, Any] = {}


class BaseParser(ABC):
    """所有解析器的统一接口。"""

    supported_extensions: set[str]

    @abstractmethod
    async def parse(self, file_path: Path) -> list[ParsedSegment]:
        """解析文件，返回段落序列。"""
