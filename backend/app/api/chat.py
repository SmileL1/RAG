"""对话路由：SSE 流式问答 + 会话/消息查询。"""
from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.conversation import Conversation
from app.models.knowledge_base import KnowledgeBase
from app.models.message import Message, MessageRole
from app.rag.generation import (
    CitationEvent,
    FinalEvent,
    GenerationService,
    TokenEvent,
    get_generation_service,
)
from app.schemas.chat import ChatRequest, ConversationOut, MessageOut
from app.schemas.common import MessageResponse
from app.services.chat_service import ChatService

router = APIRouter(
    prefix="/api/chat",
    tags=["chat"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/stream")
async def stream_chat(payload: ChatRequest, db: AsyncSession = Depends(get_db)):
    """SSE 流式问答。

    事件序列：
      event: meta      → 会话信息（conversation_id 等）
      event: token     → 每个流式 token
      event: citation  → 来源列表
      event: done      → 完成事件，含 message_id
      event: error     → 异常时
    """
    kb = await db.get(KnowledgeBase, payload.kb_id)
    if not kb:
        raise HTTPException(404, "知识库不存在")

    conv = await ChatService.get_or_create_conversation(
        db=db,
        conversation_id=payload.conversation_id,
        kb_id=payload.kb_id,
        first_question=payload.question,
    )

    history_msgs = await ChatService.get_history(db, conv.id, limit=10)
    history_for_llm = [{"role": m.role, "content": m.content} for m in history_msgs]

    # 先把用户消息落库
    user_msg = await ChatService.append_message(
        db=db,
        conversation_id=conv.id,
        role=MessageRole.USER,
        content=payload.question,
    )

    use_hyde_override = payload.use_hyde
    generation = get_generation_service()
    if use_hyde_override is not None:
        generation = GenerationService(
            retrieval_service=generation._retrieval,
            llm=generation._llm,
            use_hyde=use_hyde_override,
        )

    async def event_stream() -> AsyncIterator[bytes]:
        # meta
        yield _sse(
            "meta",
            {"conversation_id": conv.id, "user_message_id": user_msg.id},
        )

        full_answer = ""
        citations_payload: list[dict] = []

        try:
            async for ev in generation.stream_answer(
                query=payload.question,
                kb_id=payload.kb_id,
                history=history_for_llm,
            ):
                if isinstance(ev, TokenEvent):
                    full_answer += ev.content
                    yield _sse("token", {"content": ev.content})
                elif isinstance(ev, CitationEvent):
                    citations_payload = [c.model_dump() for c in ev.citations]
                    yield _sse("citation", {"citations": citations_payload})
                elif isinstance(ev, FinalEvent):
                    # 落库 assistant 消息
                    async with AsyncSessionLocal() as bg_db:
                        msg = await ChatService.append_message(
                            db=bg_db,
                            conversation_id=conv.id,
                            role=MessageRole.ASSISTANT,
                            content=ev.answer,
                            citations=[c.model_dump() for c in ev.citations],
                        )
                    yield _sse(
                        "done",
                        {
                            "message_id": msg.id,
                            "conversation_id": conv.id,
                            "chunks_used": ev.chunks_used,
                        },
                    )
        except Exception as e:
            logger.exception("SSE 流式异常: {}", e)
            yield _sse("error", {"message": str(e)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # nginx 不缓冲
        },
    )


@router.get("/conversations", response_model=list[ConversationOut])
async def list_conversations(
    kb_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Conversation).order_by(Conversation.id.desc())
    if kb_id is not None:
        stmt = stmt.where(Conversation.kb_id == kb_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/conversations/{conv_id}/messages", response_model=list[MessageOut])
async def get_conversation_messages(conv_id: int, db: AsyncSession = Depends(get_db)):
    conv = await db.get(Conversation, conv_id)
    if not conv:
        raise HTTPException(404, "会话不存在")
    msgs = await ChatService.get_history(db, conv_id, limit=1000)
    return msgs


@router.delete("/conversations/{conv_id}", response_model=MessageResponse)
async def delete_conversation(conv_id: int, db: AsyncSession = Depends(get_db)):
    conv = await db.get(Conversation, conv_id)
    if not conv:
        raise HTTPException(404, "会话不存在")
    await db.delete(conv)
    await db.commit()
    return MessageResponse(message="已删除")


# ===== 工具 =====


def _sse(event: str, data: dict) -> bytes:
    """格式化 SSE 帧。"""
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")
