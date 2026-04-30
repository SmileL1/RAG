"""会话/消息持久化业务。"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole


class ChatService:
    @staticmethod
    async def get_or_create_conversation(
        db: AsyncSession,
        conversation_id: int | None,
        kb_id: int,
        first_question: str,
    ) -> Conversation:
        if conversation_id is not None:
            conv = await db.get(Conversation, conversation_id)
            if not conv:
                raise NotFoundError(f"会话 {conversation_id} 不存在")
            return conv
        # 新建会话；title 取问题前 30 字
        title = (first_question or "新会话").strip()[:30]
        conv = Conversation(kb_id=kb_id, title=title)
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        return conv

    @staticmethod
    async def append_message(
        db: AsyncSession,
        conversation_id: int,
        role: MessageRole,
        content: str,
        citations: list[dict[str, Any]] | None = None,
        tokens_used: int | None = None,
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=role.value,
            content=content,
            citations=citations,
            tokens_used=tokens_used,
        )
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        return msg

    @staticmethod
    async def get_history(
        db: AsyncSession, conversation_id: int, limit: int = 10
    ) -> list[Message]:
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id.desc())
            .limit(limit)
        )
        return list(reversed(result.scalars().all()))
