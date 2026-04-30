# Python Web 开发学习手册
## FastAPI · uvicorn · ASGI · 项目架构

---

## 一、从零理解：Python Web 的分层模型

在 .NET Core 里，你熟悉这个结构：

```
HTTP 请求 → Kestrel（服务器）→ ASP.NET Core（框架）→ 业务代码
```

Python Web 完全一样，只是换了名字：

```
HTTP 请求 → uvicorn（服务器）→ FastAPI（框架）→ 业务代码
```

这三层各司其职，互相解耦。你可以把 FastAPI 换成 Django，把 uvicorn 换成 hypercorn，只要它们都说 ASGI 这门语言，就能互相配合。

---

## 二、ASGI 是什么

### 从 WSGI 说起

Python Web 历史上用的是 **WSGI**（Web Server Gateway Interface），诞生于 2003 年。它是一个约定：

> "服务器"和"框架"之间怎么传递请求和响应？

WSGI 的约定非常简单：

```python
# 一个最简单的 WSGI 应用
def application(environ, start_response):
    start_response("200 OK", [("Content-Type", "text/plain")])
    return [b"Hello World"]
```

`environ` 是请求信息（字典），`start_response` 是回调函数。服务器调用这个函数，框架返回响应体。

**WSGI 的问题**：它是同步的。处理一个请求必须等上一个处理完。WebSocket、长连接、SSE（流式输出）在 WSGI 下要么做不了，要么很难做。

### ASGI 登场

**ASGI**（Asynchronous Server Gateway Interface）是 2019 年出现的继任者，专为异步设计：

```python
# 一个最简单的 ASGI 应用
async def application(scope, receive, send):
    await send({
        "type": "http.response.start",
        "status": 200,
    })
    await send({
        "type": "http.response.body",
        "body": b"Hello World",
    })
```

- `scope`：请求的元信息（类型、路径、headers 等）
- `receive`：异步函数，用来"接收"客户端发来的数据
- `send`：异步函数，用来"发送"响应给客户端

**关键区别**：ASGI 用 `async/await`，一个进程可以同时处理成千上万个连接，不需要为每个请求开一个线程。这让 WebSocket、SSE、长轮询变得自然而然。

### WSGI vs ASGI 对比

| | WSGI | ASGI |
|--|------|------|
| 模式 | 同步 | 异步 |
| 并发方式 | 多进程/多线程 | 协程（单线程高并发） |
| WebSocket | 不支持 | 原生支持 |
| SSE 流式 | 困难 | 原生支持 |
| 代表框架 | Django、Flask | FastAPI、Starlette |
| 代表服务器 | gunicorn | uvicorn、hypercorn |

---

## 三、uvicorn 详解

### uvicorn 是什么

uvicorn 是目前最主流的 ASGI 服务器，用 Python 写成，基于 `uvloop`（Linux/Mac）或 `asyncio`（Windows）实现高性能事件循环。

它的职责：
1. 监听 TCP 端口（默认 8000）
2. 解析 HTTP/1.1 和 HTTP/2 协议
3. 把请求转换成 ASGI 的 `scope/receive/send` 格式
4. 调用你的 ASGI 应用（FastAPI）
5. 把响应发回给客户端

### 常用启动参数

```bash
uvicorn app.main:app \
  --host 0.0.0.0 \        # 监听地址（0.0.0.0 表示对外开放，127.0.0.1 只本机）
  --port 8000 \            # 监听端口
  --reload \               # 开发模式：文件改动自动重启
  --reload-dir app \       # 只监听 app/ 目录（防止 .venv 改动误触发）
  --workers 4 \            # 生产模式：启动 4 个进程（--reload 时不能用）
  --log-level info         # 日志级别
```

**`app.main:app` 的含义**：
```
app.main : app
 ↑           ↑
模块路径    变量名

对应文件结构：
backend/
  app/
    main.py      ← app.main 就是这个文件
      app = FastAPI(...)  ← :app 就是这个变量
```

### 开发 vs 生产

```bash
# 开发环境：单进程，热重载
uvicorn app.main:app --reload --reload-dir app

# 生产环境：多进程，不热重载
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# 生产环境（推荐用 gunicorn 管理 uvicorn worker）
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## 四、FastAPI 详解

### FastAPI 是什么

FastAPI 是一个现代 Python Web 框架，建立在 **Starlette**（ASGI 框架）和 **Pydantic**（数据验证）之上。

核心特点：
- 用 Python 类型注解自动验证参数
- 自动生成 OpenAPI 文档（`/docs`）
- 原生支持 async/await
- 性能接近 Go 和 Node.js

### 最简单的 FastAPI 应用

```python
from fastapi import FastAPI

app = FastAPI()          # 创建应用实例

@app.get("/")            # 注册路由：GET /
async def root():
    return {"message": "Hello World"}

@app.get("/users/{user_id}")   # 路径参数
async def get_user(user_id: int):   # int 类型自动验证
    return {"user_id": user_id}
```

### 路由（Router）

大型项目不会把所有路由写在 `main.py` 里，用 `APIRouter` 拆分：

```python
# app/api/users.py
from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["用户"])

@router.get("/")
async def list_users():
    return []

@router.post("/")
async def create_user():
    return {}
```

```python
# app/main.py
from app.api import users

app = FastAPI()
app.include_router(users.router)   # 注册路由
# 现在 /users/ 和 /users POST 都生效了
```

### 请求参数的几种方式

```python
from fastapi import FastAPI, Query, Body
from pydantic import BaseModel

app = FastAPI()

# 1. 路径参数
@app.get("/items/{item_id}")
async def get_item(item_id: int):   # /items/42
    ...

# 2. 查询参数（URL ?后面的）
@app.get("/items/")
async def list_items(page: int = 1, size: int = 10):   # /items/?page=2&size=20
    ...

# 3. 请求体（POST/PUT，JSON）
class ItemCreate(BaseModel):
    name: str
    price: float

@app.post("/items/")
async def create_item(item: ItemCreate):   # body: {"name": "苹果", "price": 3.5}
    return item

# 4. Header / Cookie（用 Header、Cookie 依赖注入）
from fastapi import Header
@app.get("/me/")
async def get_me(authorization: str = Header(...)):
    ...
```

### 依赖注入（Depends）

FastAPI 最强大的特性之一。把公共逻辑（鉴权、获取数据库连接）抽成依赖，自动注入：

```python
from fastapi import Depends

# 定义一个依赖：获取当前用户
async def get_current_user(token: str = Header(...)):
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401)
    return user

# 在路由里使用
@app.get("/profile/")
async def get_profile(user = Depends(get_current_user)):
    return user   # user 自动注入，不需要手动调用
```

### 数据库连接注入（典型写法）

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

@app.get("/documents/")
async def list_documents(db: AsyncSession = Depends(get_db)):
    # db 是当次请求的数据库连接，请求结束后自动关闭
    result = await db.execute(select(Document))
    return result.scalars().all()
```

### 生命周期（lifespan）

应用启动/关闭时执行的代码，用来初始化数据库连接池、加载模型等：

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    print("服务启动，初始化资源...")
    await init_database()

    yield   # ← 这里是服务正常运行的阶段

    # 关闭时执行
    print("服务关闭，释放资源...")
    await close_database()

app = FastAPI(lifespan=lifespan)
```

### 响应类型

```python
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse

# 普通 JSON（默认）
@app.get("/data/")
async def get_data():
    return {"key": "value"}   # 自动序列化为 JSON

# 流式响应（SSE，用于 AI 流式输出）
@app.get("/stream/")
async def stream():
    async def generator():
        for chunk in ["hello", " ", "world"]:
            yield f"data: {chunk}\n\n"
    return StreamingResponse(generator(), media_type="text/event-stream")

# 文件下载
@app.get("/download/")
async def download():
    return FileResponse("./file.pdf", filename="document.pdf")
```

---

## 五、async/await 基础

FastAPI 是异步框架，理解 async/await 很重要。

### 同步 vs 异步

```python
import time, asyncio

# 同步：一个一个等
def sync_task():
    time.sleep(1)   # 等 1 秒，期间什么都做不了
    return "done"

# 异步：等待期间可以去做其他事
async def async_task():
    await asyncio.sleep(1)   # 等 1 秒，但期间事件循环可以处理其他请求
    return "done"
```

### 在 FastAPI 里的规则

```python
# 有 IO 操作（数据库、HTTP 请求、文件读写）→ 用 async def + await
@app.get("/users/")
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))   # 异步查数据库
    return result.scalars().all()

# 纯 CPU 计算，没有 IO → 可以用普通 def（FastAPI 自动放线程池）
@app.get("/compute/")
def heavy_compute():
    return sum(range(10**8))   # CPU 密集，FastAPI 自动用线程池

# 在 async 函数里调用阻塞代码 → 用 asyncio.to_thread
@app.get("/mixed/")
async def mixed():
    result = await asyncio.to_thread(blocking_function)   # 不阻塞事件循环
    return result
```

---

## 六、Python 项目架构

### 标准分层架构

```
HTTP 请求
    ↓
api/（接口层）         ← 只处理 HTTP 相关：参数解析、响应格式、鉴权
    ↓
services/（业务层）    ← 业务逻辑：流程编排、规则判断
    ↓
repositories/（数据层）← 数据库操作：增删改查（有时省略，直接在 service 里查）
    ↓
models/（模型层）      ← 数据库表结构定义
```

对应到本项目：

```
api/chat.py            ← 解析请求，调用 service，返回 SSE 流
services/chat.py       ← 编排 RAG 流程：检索→重排→生成
rag/retrieval.py       ← 向量检索逻辑
rag/rerank.py          ← 重排逻辑
models/document.py     ← Document 表定义
```

### 标准目录结构

```
project/
├── app/                        # 应用主目录
│   ├── __init__.py             # 标识这是 Python 包
│   ├── main.py                 # FastAPI 实例、路由注册、lifespan
│   │
│   ├── api/                    # 接口层（路由）
│   │   ├── __init__.py
│   │   ├── users.py            # /users 相关接口
│   │   ├── products.py         # /products 相关接口
│   │   └── deps.py             # 公共依赖（鉴权、获取 DB 等）
│   │
│   ├── core/                   # 基础设施层
│   │   ├── config.py           # 读取 .env 配置（pydantic-settings）
│   │   ├── database.py         # 数据库连接池
│   │   ├── exceptions.py       # 自定义异常类
│   │   ├── logging.py          # 日志配置
│   │   └── security.py        # JWT、密码加密
│   │
│   ├── models/                 # 数据库模型（SQLAlchemy ORM）
│   │   ├── base.py             # Base 类、公共字段（created_at 等）
│   │   ├── user.py             # users 表
│   │   └── product.py         # products 表
│   │
│   ├── schemas/                # Pydantic Schema（请求/响应的数据结构）
│   │   ├── user.py             # UserCreate、UserResponse 等
│   │   └── product.py
│   │
│   ├── services/               # 业务逻辑层
│   │   ├── user_service.py
│   │   └── product_service.py
│   │
│   └── utils/                  # 工具函数
│       └── helpers.py
│
├── alembic/                    # 数据库迁移
│   ├── versions/               # 每次迁移生成一个文件
│   └── env.py
│
├── tests/                      # 测试
│   ├── test_api/
│   └── test_services/
│
├── .env                        # 环境变量（本地配置，不提交 git）
├── .env.example                # 示例配置（提交 git，给新人参考）
├── pyproject.toml              # 项目依赖声明
├── alembic.ini                 # alembic 配置
└── README.md
```

### `__init__.py` 的作用

Python 用 `__init__.py` 标识一个目录是"包"（package），可以被 import：

```
app/
  __init__.py   ← 有这个文件，app 才能被 import
  main.py
  api/
    __init__.py ← 有这个文件，app.api 才能被 import
    users.py
```

```python
from app.api import users       # 能 import，因为有 __init__.py
from app.api.users import router  # 能 import
```

文件可以是空的，只要存在就行。

### models vs schemas 的区别

很多人容易混淆：

| | models/ | schemas/ |
|--|---------|---------|
| 用途 | 数据库表结构 | HTTP 请求/响应的数据结构 |
| 基类 | SQLAlchemy `Base` | Pydantic `BaseModel` |
| 作用 | 映射数据库表 | 数据验证和序列化 |

```python
# models/user.py（数据库表）
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String)
    hashed_password = Column(String)   # 数据库存哈希，不能返回给前端

# schemas/user.py（接口数据结构）
class UserResponse(BaseModel):
    id: int
    email: str
    # 没有 hashed_password！不暴露给前端
    class Config:
        from_attributes = True   # 允许从 ORM 对象转换
```

---

## 七、配置管理（pydantic-settings）

### .env 文件

```env
# .env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db
SECRET_KEY=your-secret-key
DEBUG=true
```

### config.py 读取配置

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    DEBUG: bool = False          # 有默认值，.env 里可以不写
    MAX_CONNECTIONS: int = 10

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()   # 自动读取 .env，类型自动转换

# 用法
print(settings.DATABASE_URL)   # str
print(settings.DEBUG)          # bool，"true" 自动转为 True
print(settings.MAX_CONNECTIONS)  # int，"10" 自动转为 10
```

---

## 八、数据库（SQLAlchemy + Alembic）

### SQLAlchemy ORM

SQLAlchemy 是 Python 最主流的 ORM（对象关系映射），把 Python 类映射到数据库表：

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200), unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
```

### 异步数据库操作

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select

engine = create_async_engine("postgresql+asyncpg://...")

async def get_users(db: AsyncSession):
    result = await db.execute(select(User).where(User.name == "张三"))
    users = result.scalars().all()   # 取出所有结果
    return users

async def create_user(db: AsyncSession, name: str, email: str):
    user = User(name=name, email=email)
    db.add(user)
    await db.commit()
    await db.refresh(user)   # 刷新，获取数据库生成的 id 等字段
    return user
```

### Alembic 数据库迁移

Alembic 是 SQLAlchemy 配套的迁移工具，类似 Django 的 `makemigrations`：

```bash
# 初始化（只做一次）
alembic init alembic

# 根据 models 变化自动生成迁移文件
alembic revision --autogenerate -m "add users table"

# 执行迁移（同步到数据库）
alembic upgrade head

# 回滚一步
alembic downgrade -1
```

---

## 九、错误处理

### 自定义异常

```python
# core/exceptions.py
class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code

# main.py 注册全局处理器
@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )

# 业务代码里使用
async def get_document(doc_id: int, db):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise AppException("文档不存在", status_code=404)
    return doc
```

---

## 十、项目启动全流程

```
1. python 解释器加载 app/main.py
   ├─ 执行顶层代码（import、os.environ 设置等）
   └─ 创建 FastAPI 实例（app = FastAPI(...)）

2. uvicorn 注册 lifespan
   └─ 进入 lifespan 的 yield 之前部分（初始化资源）

3. uvicorn 开始监听端口
   └─ INFO: Uvicorn running on http://127.0.0.1:8000

4. 收到 HTTP 请求
   ├─ uvicorn 解析 HTTP → 组装 ASGI scope/receive/send
   ├─ FastAPI 匹配路由
   ├─ 执行依赖（Depends）
   ├─ 执行路由处理函数
   └─ 返回响应

5. CTRL+C 关闭
   └─ lifespan 的 yield 之后部分（释放资源）
```

---

## 十一、与 .NET Core 的对比

### 概念对照表

| 概念 | .NET Core | Python/FastAPI |
|------|-----------|----------------|
| Web 框架 | ASP.NET Core | FastAPI |
| 内置服务器 | Kestrel | uvicorn |
| 接口协议 | 无统一协议（直接集成） | ASGI |
| ORM | Entity Framework Core | SQLAlchemy |
| 配置管理 | appsettings.json + IConfiguration | pydantic-settings + .env |
| 数据库迁移 | EF Core Migrations | Alembic |
| 包管理 | NuGet + .csproj | uv / pip + pyproject.toml |
| 依赖注入 | 内置 DI 容器（IServiceCollection） | FastAPI Depends |
| 数据验证 | Data Annotations / FluentValidation | Pydantic |
| 中间件 | Middleware（`app.UseXxx()`） | Middleware（`app.add_middleware()`） |
| 测试 | xUnit / NUnit | pytest |
| 异步模型 | async/await（Task） | async/await（协程） |
| 日志 | ILogger / Serilog | loguru / logging |

### 启动流程对比

**.NET Core（Program.cs）**：
```csharp
var builder = WebApplication.CreateBuilder(args);

// 注册服务（相当于 FastAPI 的 Depends 体系）
builder.Services.AddControllers();
builder.Services.AddDbContext<AppDbContext>();
builder.Services.AddScoped<IUserService, UserService>();

var app = builder.Build();

// 注册中间件
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();

app.Run();   // 启动 Kestrel，开始监听
```

**FastAPI（main.py）**：
```python
app = FastAPI(lifespan=lifespan)

# 注册中间件
app.add_middleware(CORSMiddleware, ...)

# 注册路由（相当于 MapControllers）
app.include_router(users.router)
app.include_router(documents.router)

# uvicorn app.main:app  ← 命令行启动，等价于 app.Run()
```

### 路由写法对比

**.NET Core Controller**：
```csharp
[ApiController]
[Route("api/[controller]")]
public class UsersController : ControllerBase
{
    [HttpGet("{id}")]
    public async Task<IActionResult> GetUser(int id)
    {
        return Ok(new { Id = id });
    }

    [HttpPost]
    public async Task<IActionResult> CreateUser([FromBody] UserCreateDto dto)
    {
        return Created(...);
    }
}
```

**FastAPI**：
```python
router = APIRouter(prefix="/api/users", tags=["用户"])

@router.get("/{id}")
async def get_user(id: int):          # 路径参数自动解析
    return {"id": id}

@router.post("/")
async def create_user(dto: UserCreateDto):   # Body 自动解析和验证
    return dto
```

### 依赖注入对比

**.NET Core** 在 `Program.cs` 集中注册，框架自动注入构造函数：
```csharp
// 注册
builder.Services.AddScoped<IUserService, UserService>();

// 使用（构造函数注入）
public class UsersController(IUserService userService) { ... }
```

**FastAPI** 用 `Depends()` 在路由函数参数上声明，按需注入：
```python
# 定义依赖
async def get_current_user(token: str = Header(...)) -> User:
    return verify_token(token)

# 使用（参数注入）
@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return user
```

两者思路相同（都是 IoC），只是声明方式不同：.NET 是集中注册，FastAPI 是就地声明。

### 数据验证对比

**.NET Core（Data Annotations）**：
```csharp
public class UserCreateDto
{
    [Required]
    [MaxLength(100)]
    public string Name { get; set; }

    [EmailAddress]
    public string Email { get; set; }

    [Range(0, 150)]
    public int Age { get; set; }
}
```

**FastAPI（Pydantic）**：
```python
from pydantic import BaseModel, EmailStr, Field

class UserCreateDto(BaseModel):
    name: str = Field(..., max_length=100)
    email: EmailStr
    age: int = Field(..., ge=0, le=150)
```

验证失败时都自动返回 400 Bad Request，不需要手动写 if 判断。

### 配置管理对比

**.NET Core（appsettings.json）**：
```json
{
  "ConnectionStrings": {
    "Default": "Server=...;Database=..."
  },
  "JwtSettings": {
    "SecretKey": "xxx",
    "ExpireMinutes": 60
  }
}
```
```csharp
var connStr = configuration.GetConnectionString("Default");
```

**FastAPI（.env + pydantic-settings）**：
```env
DATABASE_URL=postgresql://...
JWT_SECRET_KEY=xxx
JWT_EXPIRE_MINUTES=60
```
```python
class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_EXPIRE_MINUTES: int = 60

settings = Settings()   # 自动读取 .env
```

### 中间件对比

**.NET Core**：
```csharp
app.Use(async (context, next) => {
    // 请求前
    Console.WriteLine($"Request: {context.Request.Path}");
    await next();
    // 响应后
    Console.WriteLine($"Response: {context.Response.StatusCode}");
});
```

**FastAPI**：
```python
@app.middleware("http")
async def log_middleware(request: Request, call_next):
    print(f"Request: {request.url.path}")
    response = await call_next(request)
    print(f"Response: {response.status_code}")
    return response
```

结构几乎一模一样。

### 关键差异点

| 差异 | .NET Core | FastAPI |
|------|-----------|---------|
| 运行时 | CLR（编译型） | CPython（解释型） |
| 启动速度 | 慢（JIT 预热） | 快 |
| 性能 | 极高 | 高（接近） |
| 类型系统 | 强类型（编译期检查） | 动态类型（运行时检查） |
| GIL | 无 | 有（多线程 CPU 密集受限） |
| 部署 | 单一可执行文件 / Docker | 需要 Python 环境 / Docker |
| 生态 | NuGet（成熟） | PyPI（庞大，AI/ML 无敌） |

---

*文档生成时间：2026-04-28*
