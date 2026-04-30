"""导出所有模型，方便 Alembic 自动发现。"""
from app.models.base import Base, TimestampMixin
from app.models.chunk import Chunk
from app.models.conversation import Conversation
from app.models.document import Document, DocumentStatus
from app.models.knowledge_base import KnowledgeBase
from app.models.message import Message, MessageRole

__all__ = [
    "Base",
    "Chunk",
    "Conversation",
    "Document",
    "DocumentStatus",
    "KnowledgeBase",
    "Message",
    "MessageRole",
    "TimestampMixin",
]
