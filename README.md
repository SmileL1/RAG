# RAG 私有知识库系统

> 基于 FastAPI + Qdrant + Vue3 的私有文档问答系统。
> 上传文档，登录后用自然语言提问，AI 给出带原文溯源的流式回答。

## 核心特性

- **多格式文档**：PDF · Word · Markdown · TXT · HTML
- **语义检索 + Rerank**：Qdrant 向量检索（Top-10）→ bge-reranker-v2-m3 精排（Top-5）
- **流式问答（SSE）**：边生成边显示，答案附带原文溯源（相关度按本次结果相对归一化展示）
- **原文溯源查看**：点击任一引用，右侧抽屉展示该文档**完整原文**并**黄色高亮命中段**、自动定位，可下载原文件
- **Embedding 双通道**：阿里云 DashScope API / 本地 bge-m3，`.env` 一键切换
- **LLM 可插拔**：DeepSeek / OpenAI / 通义 / Kimi / **Ollama 本地**，统一走 OpenAI 兼容协议
- **页面内配置 LLM**：设置页直接切换供应商（含预设）、改地址/模型/Key、**测试连接**，保存即时生效并写回 `.env`（重启不丢）
- **JWT 登录鉴权**：所有 API 受保护，token 7 天有效
- **用户管理**：Admin 可创建账号、重置密码、启用/禁用、升降权限
- **多知识库**：按项目/主题独立管理，互不干扰
- **当代 SaaS 亮色 UI**：紫罗兰（#5B4FE8）accent + 锐利卡片 + 76px 图标导航轨

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.11 · FastAPI · SQLAlchemy（异步）· Alembic |
| RAG | LlamaIndex 分块 · FlagEmbedding（bge-m3）· Qdrant · bge-reranker-v2-m3 |
| LLM | DeepSeek / OpenAI / 通义 / Kimi / Ollama（统一 OpenAI 兼容协议） |
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

## 在设置页配置 LLM（含 Ollama 本地）

除了改 `.env`，登录后可在 **设置页** 直接配置 LLM，**保存即时生效并写回 `.env`**（重启依然生效）：

- **供应商预设**：选「DeepSeek / 通义千问(DashScope) / Kimi / OpenAI / Ollama 本地 / 自定义」会自动填好 API 地址与默认模型，仍可手动改。
- **API Key**：密码态输入、读取时遮蔽（只显示 `sk-xx****xxxx`）；Ollama 本地无需 Key，留空即可。
- **测试连接**：用当前配置发一次最小调用，确认地址/模型/Key 是否连通。

### 用 Ollama 跑本地模型（离线、不花钱）

1. 安装并启动 [Ollama](https://ollama.com)，拉一个模型，例如：
   ```bash
   ollama pull qwen2.5:3b      # 或 qwen2.5:1.5b（更快）/ gemma3 等
   ```
2. 设置页 → 供应商选 **Ollama 本地**（地址自动填 `http://localhost:11434/v1`）→ 点「刷新」→ 模型下拉里选刚拉的模型 → Key 留空 → 保存 → 测试连接。

> 说明：Gemini 等是闭源云端模型（需联网/代理）；想本地离线请用 Ollama + 开源模型（Qwen / Gemma 等）。纯 CPU 推理建议选 1.5B~3B 量化模型。

## Docker 部署（生产）

Docker Compose 一键拉起全部服务：PostgreSQL · Redis · Qdrant · 后端 · 前端 · Nginx。

### 前置条件

- Docker 20.10+（含 Docker Compose v2）
- API Key：DeepSeek（LLM）、阿里云 DashScope（Embedding，或改用本地 bge-m3 则无需）

### 第一步：准备配置文件

```bash
cd deploy
cp .env.production.example .env.production
```

编辑 `.env.production`，**必填项**：

| 变量 | 说明 |
|------|------|
| `JWT_SECRET` | 随机长字符串，至少 32 位 |
| `ADMIN_PASSWORD` | 管理员初始密码 |
| `POSTGRES_PASSWORD` | 数据库密码（同时更新 `DATABASE_URL` 中的密码） |
| `DASHSCOPE_API_KEY` | 阿里云 DashScope Key（使用 `dashscope` Embedding 时必填） |
| `LLM_API_KEY` | LLM 服务 Key |
| `CORS_ORIGINS` | 允许访问的前端地址，如 `http://your-server-ip` |

### 第二步：启动服务

```bash
# 标准模式（INGEST_MODE=sync，无需 Celery，推荐）
docker compose --env-file .env.production up -d

# 如需独立 Celery Worker（INGEST_MODE=celery 时）
docker compose --env-file .env.production --profile celery up -d
```

> **首次启动说明**：后端会自动下载 bge-reranker-v2-m3（约 2GB）并运行 Alembic 迁移建表，
> 启动完成约需 3~5 分钟。可通过 `docker logs -f rag-backend` 观察进度。

### 第三步：访问

| 地址 | 说明 |
|------|------|
| `http://your-server-ip:8080` | 前端页面（Nginx 代理） |
| `http://your-server-ip:8000/docs` | 后端 Swagger UI |

默认管理员：`admin` / `.env.production` 中设置的 `ADMIN_PASSWORD`。

### 常用运维命令

```bash
# 查看所有服务状态
docker compose --env-file .env.production ps

# 查看后端日志
docker logs -f rag-backend

# 停止所有服务
docker compose --env-file .env.production down

# 停止并删除数据卷（⚠️ 会清空数据库和向量库）
docker compose --env-file .env.production down -v

# 重新构建镜像（代码更新后）
docker compose --env-file .env.production build
docker compose --env-file .env.production up -d
```

### 数据持久化

Compose 文件声明了以下具名卷，数据在容器重建后不丢失：

| 卷名 | 内容 |
|------|------|
| `pg_data` | PostgreSQL 数据 |
| `qdrant_data` | Qdrant 向量数据 |
| `uploads` | 用户上传的原始文件 |
| `hf_cache` | HuggingFace 模型缓存（bge-reranker，避免重复下载） |
| `ollama_data` | Ollama 模型缓存（避免每次重启重新下载） |

---

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
# 这组（供应商/地址/模型/Key）与下方检索参数也可在「设置页」运行时修改并写回本文件
LLM_PROVIDER=deepseek                              # deepseek | openai | qwen | kimi | ollama | 自定义
LLM_API_BASE=https://api.deepseek.com/v1          # Ollama 本地：http://localhost:11434/v1
LLM_API_KEY=sk-xxx                                # Ollama 本地可填任意占位（如 ollama）
LLM_MODEL=deepseek-chat                           # Ollama 例：qwen2.5:3b

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
- [x] 原文溯源查看（点击引用 → 右侧抽屉看完整原文 + 命中高亮 + 下载原文件）
- [x] 设置页运行时配置 LLM（供应商预设 / API Key 遮蔽 / 测试连接 / 写回 .env）
- [x] Ollama 本地模型支持（列出本机已装模型，下拉直选）
- [x] 分块优化（Markdown 按 H1/H2 切节 + 通用碎块合并，避免「只含标题」的小块）
- [x] 当代 SaaS 亮色 UI（紫罗兰 accent，全站统一）
- [x] Reranker 性能优化（max_length=256 + 启动预热）
- [x] Alembic 迁移完整（5 版本：init → 扩展字段 → users → is_admin）
- [x] 生产部署（Docker Compose）

## 文档

- [详细设计方案](docs/设计方案.md) — 技术选型、模块关系、Prompt 模板
- [开发指南](docs/开发指南.md) — 环境搭建、常见问题

## License

私有项目，未授权请勿传播。
