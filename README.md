# RAG 私有知识库系统

> 基于 FastAPI + Qdrant + Vue3 的私有文档问答系统。
> 上传文档，登录后用自然语言提问，AI 给出带原文溯源的流式回答。

## 核心特性

- **多格式文档**：PDF · Word · Markdown · TXT · HTML
- **语义检索 + Rerank**：Qdrant 向量检索（Top-10）→ bge-reranker-v2-m3 精排（Top-5）
- **流式问答（SSE）**：边生成边显示，答案附带原文溯源（含相关度百分比）
- **Embedding 双通道**：阿里云 DashScope API / 本地 bge-m3，`.env` 一键切换
- **LLM 可插拔**：DeepSeek / OpenAI / 通义 / Kimi，兼容 OpenAI 协议
- **JWT 登录鉴权**：所有 API 受保护，token 7 天有效
- **用户管理**：Admin 可创建账号、重置密码、启用/禁用、升降权限
- **多知识库**：按项目/主题独立管理，互不干扰
- **亮色 UI**：蓝白玻璃态主题

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.11 · FastAPI · SQLAlchemy（异步）· Alembic |
| RAG | FlagEmbedding（bge-m3）· Qdrant · bge-reranker-v2-m3 |
| LLM | DeepSeek（via OpenAI 兼容协议） |
| 认证 | JWT（python-jose）· bcrypt 密码哈希 |
| 前端 | Vue 3 · TypeScript · Vite · Pinia · Naive UI |
| 存储 | PostgreSQL（元数据 + 用户）· Qdrant（向量） |

## 快速开始（本地开发，Windows）

### 前置条件

| 软件 | 说明 |
|------|------|
| Python 3.11+ | https://www.python.org/downloads/ |
| uv | `powershell -c "irm https://astral.sh/uv/install.ps1 \| iex"` |
| PostgreSQL 16 | https://www.postgresql.org/download/windows/ |
| Node.js 20+ | https://nodejs.org/ |

API Key：

| 服务 | 用途 |
|------|------|
| DeepSeek | LLM 问答 |
| 阿里云 DashScope | Embedding（也可改用本地 bge-m3，无需 Key） |

### 第一步：初始化数据库

```sql
-- psql 里执行
CREATE USER rag_user WITH PASSWORD 'rag_pass';
CREATE DATABASE rag_db OWNER rag_user;
```

### 第二步：配置后端

```powershell
cd backend
uv sync                    # 安装 Python 依赖
copy .env.example .env     # 复制配置模板
# 编辑 .env，至少填写：
# DASHSCOPE_API_KEY / LLM_API_KEY / JWT_SECRET
```

### 第三步：建表

```powershell
cd backend
.venv\Scripts\alembic upgrade head
# 建立所有表（知识库/文档/对话/消息/用户）
# 首次启动后端时会自动创建默认管理员账号
```

### 第四步：启动服务

**终端 1 — 后端 API：**
```powershell
cd backend
.venv\Scripts\uvicorn app.main:app --reload --reload-dir app
# http://localhost:8000/docs — Swagger UI
```

> 首次启动会自动加载 bge-reranker-v2-m3（约 2GB），初始化完成约需 1~3 分钟。
> 启动日志显示 `✅ 已创建默认管理员账号: admin / admin123` 即表示初始化成功。

**终端 2 — 前端：**
```powershell
cd frontend
npm install
npm run dev
# http://localhost:5173
```

### 第五步：登录

打开 http://localhost:5173，使用默认账号登录：

| 字段 | 值 |
|------|-----|
| 用户名 | `admin` |
| 密码 | `admin123` |

**请登录后立即在「用户管理」页修改 admin 密码。**

## 环境变量说明（.env）

```dotenv
# ===== 数据库 =====
DATABASE_URL=postgresql+asyncpg://rag_user:rag_pass@localhost:5432/rag_db

# ===== Qdrant =====
QDRANT_MODE=local                 # local=文件内嵌，remote=连接 Qdrant 服务
QDRANT_LOCAL_PATH=./data/qdrant

# ===== Embedding（二选一）=====
EMBEDDING_PROVIDER=dashscope      # dashscope | local_bge
DASHSCOPE_API_KEY=sk-xxx

# ===== LLM =====
LLM_PROVIDER=deepseek
LLM_API_BASE=https://api.deepseek.com/v1
LLM_API_KEY=sk-xxx
LLM_MODEL=deepseek-chat

# ===== JWT 认证 =====
JWT_SECRET=请修改为随机长字符串
JWT_EXPIRE_DAYS=7
ADMIN_USERNAME=admin              # 默认管理员用户名（首次启动自动创建）
ADMIN_PASSWORD=admin123           # 默认管理员密码（请尽快修改）

# ===== Reranker =====
RERANK_ENABLED=true
RERANKER_MODEL=BAAI/bge-reranker-v2-m3
RERANK_TOP_K=5                    # rerank 后保留条数
RETRIEVE_TOP_K=10                 # 向量搜索召回条数

# ===== 入库模式 =====
INGEST_MODE=sync                  # sync 不需要 Celery，本地开发推荐
```

## API 鉴权

所有业务接口（`/api/kb/*`、`/api/chat/*`、`/api/documents/*`、`/api/admin/*`）均需在请求头带 JWT Token：

```
Authorization: Bearer <access_token>
```

Token 通过 `POST /api/auth/login` 获取。`/api/auth/login` 和 `/health` 无需鉴权。

`/api/admin/*` 接口额外要求登录用户的 `is_admin=true`，普通用户调用返回 403。

## 用户管理

Admin 登录后，侧边栏显示「用户管理」入口，支持：

| 操作 | 说明 |
|------|------|
| 创建用户 | 填用户名 + 密码（留空则自动生成随机密码并一次性展示） |
| 重置密码 | 生成新随机密码，展示一次后不可再查 |
| 启用/禁用 | 禁用后该用户无法登录 |
| 升/降管理员 | 切换 `is_admin` 权限 |
| 删除用户 | 不可删除自己 |

## 项目状态

- [x] 后端 RAG 引擎（解析 / 分块 / Embedding / 检索 / Rerank / 流式生成）
- [x] JWT 登录鉴权 + 用户管理
- [x] 前端完整功能（知识库 / 文档上传 / 流式对话 / 引用溯源）
- [x] Reranker 性能优化（max_length=256 + 启动预热）
- [x] Alembic 迁移完整（5 版本：init → 扩展字段 → users → is_admin）
- [ ] 生产部署（Docker Compose）

## 文档

- [详细设计方案](docs/设计方案.md) — 技术选型、模块关系、Prompt 模板
- [开发指南](docs/开发指南.md) — 环境搭建、常见问题

## License

私有项目，未授权请勿传播。
