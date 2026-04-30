"""Chunker 测试。"""
from __future__ import annotations

from app.rag.chunker import Chunker
from app.rag.parsers.base import ParsedSegment


def test_chunker_short_text_one_chunk():
    chunker = Chunker(chunk_size=512, chunk_overlap=50)
    segments = [ParsedSegment(text="短文本，不会切。", metadata={"page": 1, "filename": "a.pdf"})]
    chunks = chunker.chunk(segments)
    assert len(chunks) == 1
    assert "短文本" in chunks[0].text
    assert chunks[0].metadata["page"] == 1
    assert chunks[0].metadata["filename"] == "a.pdf"
    assert chunks[0].metadata["chunk_idx"] == 0
    assert chunks[0].metadata["sub_chunk_idx"] == 0


def test_chunker_long_text_multiple_chunks():
    chunker = Chunker(chunk_size=80, chunk_overlap=10)
    long_text = "这是一个测试句子。" * 50  # ~500 chars
    segments = [ParsedSegment(text=long_text, metadata={})]
    chunks = chunker.chunk(segments)
    assert len(chunks) > 1
    # chunk_idx 全局连续
    for i, c in enumerate(chunks):
        assert c.metadata["chunk_idx"] == i


def test_chunker_preserves_per_segment_metadata():
    chunker = Chunker(chunk_size=512, chunk_overlap=50)
    segments = [
        ParsedSegment(text="第一页内容", metadata={"page": 1, "filename": "a.pdf"}),
        ParsedSegment(text="第二页内容", metadata={"page": 2, "filename": "a.pdf"}),
        ParsedSegment(text="第三页内容", metadata={"page": 3, "filename": "a.pdf"}),
    ]
    chunks = chunker.chunk(segments)
    assert len(chunks) == 3
    pages = [c.metadata["page"] for c in chunks]
    assert pages == [1, 2, 3]


def test_chunker_global_index_across_segments():
    chunker = Chunker(chunk_size=40, chunk_overlap=5)
    segments = [
        ParsedSegment(text="句一。" * 20, metadata={"page": 1}),
        ParsedSegment(text="句二。" * 20, metadata={"page": 2}),
    ]
    chunks = chunker.chunk(segments)
    assert len(chunks) > 2
    indices = [c.metadata["chunk_idx"] for c in chunks]
    assert indices == sorted(indices)
    assert indices[0] == 0
    assert indices[-1] == len(chunks) - 1


def test_chunker_skips_empty_segments():
    chunker = Chunker(chunk_size=100, chunk_overlap=10)
    segments = [
        ParsedSegment(text="", metadata={}),
        ParsedSegment(text="   \n  ", metadata={}),
        ParsedSegment(text="有内容", metadata={"page": 5}),
    ]
    chunks = chunker.chunk(segments)
    assert len(chunks) == 1
    assert chunks[0].metadata["page"] == 5
