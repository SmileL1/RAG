# RAG Backend

> FastAPI + SQLAlchemy + Celery + LlamaIndex + Qdrant 的 RAG 后端

## 当前状态（M1+M2 完成）
- ✅ 项目骨架、配置层、日志、异常
- ✅ 数据模型（KnowledgeBase / Document / Chunk / Conversation / Message）
- ✅ Pydantic Schemas
- ✅ FastAPI 入口 + CORS + lifespan
- ✅ 路由占位（KB CRUD 已可用，文档/对话路由 501 占位）
- ✅ Alembic 异步迁移配置
- ✅ Celery 实例
- ✅ RAG 模块抽象基类（Embedder / LLM / Parser）
- ✅ Prompt 模板
- ⏳ Embedder/LLM 具体实现（M3）
- ⏳ Qdrant 接入（M4）
- ⏳ 文档解析+分块（M5）
- ⏳ 异步入库任务（M6）
- ⏳ 检索+Rerank（M7）
- ⏳ 流式生成（M8）

## 启动步骤

### 1. 安装依赖
```powershell
cd backend
uv sync
```

### 2. 配置
```powershell
copy .env.example .env
# 用编辑器打开 .env，填入：
#   DATABASE_URL（PG 连接串）
#   DASHSCOPE_API_KEY（阿里云 Embedding）
#   LLM_API_KEY（DeepSeek API Key）
```

### 3. 准备 PostgreSQL（本地原生安装后）
```sql
-- 在 psql 里执行
CREATE USER rag_user WITH PASSWORD 'rag_pass';
CREATE DATABASE rag_db OWNER rag_user;
```

### 4. 数据库迁移
```powershell
uv run alembic revision --autogenerate -m "init"
uv run alembic upgrade head
```

### 5. 启动 API
```powershell
uv run uvicorn app.main:app --reload --port 8000
```

访问 http://localhost:8000/docs 查看 Swagger UI。

### 6. 启动 Celery Worker（新终端，Windows 必须用 -P solo）
```powershell
uv run celery -A app.tasks.celery_app worker -l info -P solo
```

## 测试
```powershell
uv run pytest -v
```

## 目录约定
- `app/core/` — 配置、日志、DB、异常等基础设施
- `app/models/` — SQLAlchemy ORM
- `app/schemas/` — Pydantic DTO
- `app/api/` — FastAPI 路由
- `app/services/` — 业务逻辑层
- `app/rag/` — RAG 核心引擎（embedders / llm / parsers / chunker / retrieval / generation）
- `app/tasks/` — Celery 异步任务
- `app/wecom/` — 企业微信集成（v2）
- `alembic/` — 数据库迁移脚本
- `tests/` — pytest 测试
