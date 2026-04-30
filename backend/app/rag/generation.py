"""生成服务：把检索结果 + Prompt 模板拼起来，调用 LLM 流式回答。

事件类型：
  - TokenEvent       每个流式 token
  - CitationEvent    流结束前一次性给出溯源
  - 完整答案/最终落库交由 API 层处理（service 不直接接 DB）
"""
from __future__ import annotations

from collections.abc import AsyncIterator

from loguru import logger
from pydantic import BaseModel

from app.rag.citation import extract_citations
from app.rag.llm.base import BaseLLM
from app.rag.prompt import (
    HYDE_PROMPT_TEMPLATE,
    RAG_SYSTEM_PROMPT,
    RAG_USER_PROMPT_TEMPLATE,
)
from app.rag.retrieval import RetrievalService
from app.rag.vector_store import SearchResult
from app.schemas.chat import Citation


class TokenEvent(BaseModel):
    type: str = "token"
    content: str


class CitationEvent(BaseModel):
    type: str = "citation"
    citations: list[Citation]


class FinalEvent(BaseModel):
    """流式生成结束后的总结，包含完整答案文本和检索片段，供上层落库。"""

    type: str = "final"
    answer: str
    citations: list[Citation]
    chunks_used: int


GenerationEvent = TokenEvent | CitationEvent | FinalEvent


class GenerationService:
    def __init__(
        self,
        retrieval_service: RetrievalService,
        llm: BaseLLM,
        use_hyde: bool = False,
    ):
        self._retrieval = retrieval_service
        self._llm = llm
        self._use_hyde = use_hyde

    async def stream_answer(
        self,
        query: str,
        kb_id: int,
        *,
        history: list[dict[str, str]] | None = None,
        doc_ids: list[int] | None = None,
    ) -> AsyncIterator[GenerationEvent]:
        """流式回答用户问题，依次产出 Token / Citation / Final 事件。"""
        history = history or []
        retrieve_query = query

        # 1. （可选）HyDE
        if self._use_hyde:
            try:
                hyde_messages = [
                    {"role": "user", "content": HYDE_PROMPT_TEMPLATE.format(question=query)}
                ]
                fake_doc = await self._llm.chat(hyde_messages, temperature=0.7, max_tokens=300)
                if fake_doc.strip():
                    retrieve_query = fake_doc
                    logger.debug("HyDE 已生成假答案 (len={})", len(fake_doc))
            except Exception as e:
                logger.warning("HyDE 失败，回退用原 query 检索: {}", e)

        # 2. 检索（含 rerank），完成后再开始生成
        chunks: list[SearchResult] = await self._retrieval.retrieve(
            retrieve_query, kb_id, doc_ids=doc_ids
        )
        citations = extract_citations(chunks)

        # 3. 拼 Prompt
        if not chunks:
            no_match_msg = "根据已有资料，我没有找到相关内容来回答这个问题。请尝试换种问法，或确认相关文档已上传。"
            yield TokenEvent(content=no_match_msg)
            yield CitationEvent(citations=[])
            yield FinalEvent(answer=no_match_msg, citations=[], chunks_used=0)
            return

        context = self._format_context(chunks)
        messages: list[dict[str, str]] = [{"role": "system", "content": RAG_SYSTEM_PROMPT}]
        messages.extend(history[-6:])
        messages.append(
            {
                "role": "user",
                "content": RAG_USER_PROMPT_TEMPLATE.format(context=context, question=query),
            }
        )

        # 4. 流式调 LLM
        full_answer = ""
        async for token in self._llm.stream_chat(messages):
            full_answer += token
            yield TokenEvent(content=token)

        # 5. 收尾
        yield CitationEvent(citations=citations)
        yield FinalEvent(answer=full_answer, citations=citations, chunks_used=len(chunks))

    @staticmethod
    def _format_context(chunks: list[SearchResult]) -> str:
        lines = []
        for i, c in enumerate(chunks, start=1):
            meta = c.metadata or {}
            filename = meta.get("filename", "未知文件")
            page = meta.get("page")
            section = meta.get("section")
            loc_parts = [f"《{filename}》"]
            if page:
                loc_parts.append(f"第 {page} 页")
            if section:
                loc_parts.append(f"〈{section}〉")
            loc = " · ".join(loc_parts)
            lines.append(f"[{i}] (来自 {loc})\n{c.text}")
        return "\n\n".join(lines)


def get_generation_service() -> GenerationService:
    from app.core.config import settings
    from app.rag.llm.factory import get_llm
    from app.rag.retrieval import get_retrieval_service

    return GenerationService(
        retrieval_service=get_retrieval_service(),
        llm=get_llm(),
        use_hyde=settings.USE_HYDE,
    )
