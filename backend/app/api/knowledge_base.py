"""知识库路由：DB 元数据 + Qdrant collection 联动。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.knowledge_base import KnowledgeBase
from app.rag.embedders.factory import get_embedder
from app.rag.vector_store import get_vector_store
from app.schemas.common import MessageResponse
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseOut, KnowledgeBaseUpdate

router = APIRouter(
    prefix="/api/kb",
    tags=["knowledge-base"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=KnowledgeBaseOut, status_code=status.HTTP_201_CREATED)
async def create_kb(payload: KnowledgeBaseCreate, db: AsyncSession = Depends(get_db)):
    embedder = get_embedder()
    kb = KnowledgeBase(
        name=payload.name,
        description=payload.description,
        embedding_model=embedder.name,
        embedding_dim=embedder.dimension,
    )
    db.add(kb)
    await db.commit()
    await db.refresh(kb)

    # 同步创建 Qdrant collection
    store = get_vector_store()
    await store.ensure_collection(kb.collection_name, dimension=embedder.dimension)
    logger.info("KB 创建完成 id={} collection={}", kb.id, kb.collection_name)
    return kb


@router.get("", response_model=list[KnowledgeBaseOut])
async def list_kb(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(KnowledgeBase).order_by(KnowledgeBase.id.desc()))
    return result.scalars().all()


@router.get("/{kb_id}", response_model=KnowledgeBaseOut)
async def get_kb(kb_id: int, db: AsyncSession = Depends(get_db)):
    kb = await db.get(KnowledgeBase, kb_id)
    if not kb:
        raise HTTPException(404, "知识库不存在")
    return kb


@router.patch("/{kb_id}", response_model=KnowledgeBaseOut)
async def update_kb(kb_id: int, payload: KnowledgeBaseUpdate, db: AsyncSession = Depends(get_db)):
    kb = await db.get(KnowledgeBase, kb_id)
    if not kb:
        raise HTTPException(404, "知识库不存在")
    if payload.name is not None:
        kb.name = payload.name
    if payload.description is not None:
        kb.description = payload.description
    await db.commit()
    await db.refresh(kb)
    return kb


@router.delete("/{kb_id}", response_model=MessageResponse)
async def delete_kb(kb_id: int, db: AsyncSession = Depends(get_db)):
    kb = await db.get(KnowledgeBase, kb_id)
    if not kb:
        raise HTTPException(404, "知识库不存在")
    collection = kb.collection_name
    await db.delete(kb)
    await db.commit()

    store = get_vector_store()
    await store.delete_collection(collection)
    logger.info("KB 已删除 id={} collection={}", kb_id, collection)
    return MessageResponse(message="已删除")
