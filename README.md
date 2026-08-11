# FastAPI 通用后台管理系统

基于 FastAPI + SQLAlchemy 2.0 + Pydantic v2 构建的通用后台管理系统，包含用户管理、RBAC 权限控制、博客文章/评论/标签等完整功能。适合作为简历核心项目。

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | >=0.110,<0.116 | Web 框架 |
| SQLAlchemy | >=2.0 | ORM |
| SQLite | 内置 | 数据库 |
| Pydantic | >=2.6 | 数据校验 |
| pydantic-settings | latest | 环境变量管理 |
| python-jose | latest | JWT 生成/校验 |
| passlib + bcrypt | 4.0.x | 密码哈希 |
| python-multipart | latest | 表单解析 |
| uvicorn | latest | ASGI 服务器 |
| loguru | latest | 日志 |
| pytest + httpx | latest | 测试 |

## 项目结构

```
fastapi-admin-system/
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI 应用入口
│   ├── core/                 # 核心模块
│   │   ├── config.py         # 配置管理(pydantic-settings)
│   │   ├── security.py       # JWT + 密码哈希
│   │   └── logging.py        # loguru 日志配置
│   ├── db/                   # 数据库
│   │   ├── database.py       # engine/Session
│   │   └── base.py           # DeclarativeBase
│   ├── models/               # ORM 模型
│   │   ├── user.py           # 用户
│   │   ├── role.py           # 角色 + 权限
│   │   ├── article.py        # 文章
│   │   ├── comment.py        # 评论
│   │   └── tag.py            # 标签
│   ├── schemas/              # Pydantic 模型
│   │   ├── auth.py           # 认证相关
│   │   ├── user.py           # 用户相关
│   │   ├── article.py        # 文章相关
│   │   └── common.py         # 通用(分页/统一响应)
│   ├── api/
│   │   ├── deps.py           # 依赖注入(get_db/get_current_user/require_roles)
│   │   └── v1/
│   │       ├── auth.py       # 注册/登录/刷新/当前用户
│   │       ├── users.py      # 用户CRUD(admin)
│   │       └── articles.py   # 文章CRUD+评论+标签
│   ├── services/             # 业务逻辑层
│   │   ├── user_service.py   # 用户业务
│   │   └── article_service.py# 文章业务
│   └── utils/                # 工具
│       ├── exceptions.py     # 自定义异常 + 全局handler
│       ├── pagination.py     # 分页工具
│       └── response.py       # 统一响应
├── tests/                    # 测试
│   ├── conftest.py           # 测试配置(TestClient+内存sqlite)
│   ├── test_auth.py          # 认证测试
│   ├── test_articles.py      # 文章测试
│   └── test_rbac.py          # RBAC测试
├── requirements.txt
├── .gitignore
├── .env.example
├── README.md
├── 接口文档.md
├── start.sh
├── start.bat
└── pytest.ini
```

## 快速开始

### 一键启动

```bash
# Linux / macOS
bash start.sh

# Windows
start.bat
```

启动后访问 http://127.0.0.1:8000/docs 查看 Swagger API 文档。

### 手动启动

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate    # Linux/macOS
# venv\Scripts\activate     # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 复制配置文件
cp .env.example .env
# 编辑 .env 修改密钥等配置

# 4. 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 使用 uv 启动

```bash
uv venv
uv pip install -r requirements.txt
uv run uvicorn app.main:app --reload
```

## 默认账号

应用启动时会自动创建管理员账号（仅首次）：

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | （从 .env 的 ADMIN_PASSWORD 读取） | admin |

> 请务必在首次部署后修改 .env 中的 ADMIN_PASSWORD 为强密码。

## 功能模块

### 1. 认证模块

- **注册**：`POST /api/v1/auth/register`（用户名+邮箱+密码，密码 bcrypt 哈希）
- **登录（OAuth2表单）**：`POST /api/v1/auth/login`（兼容 Swagger Authorize）
- **登录（JSON）**：`POST /api/v1/auth/login/json`（支持用户名或邮箱登录）
- **刷新Token**：`POST /api/v1/auth/refresh`（使用 refresh_token）
- **当前用户**：`GET /api/v1/auth/me`（需 Bearer Token）

### 2. RBAC 权限控制

- 三种内置角色：`admin`（全部权限）、`editor`（文章读写）、`user`（只读+评论）
- `require_roles` 依赖实现角色校验
- 用户管理接口仅 admin 可访问

### 3. 用户管理（admin）

- 用户列表（分页）
- 创建用户
- 用户详情
- 更新用户（含角色变更）
- 删除用户

### 4. 博客模块

- **文章 CRUD**：创建/列表/详情/更新/删除
- **分页搜索**：支持关键字搜索（标题/摘要）、按标签筛选
- **评论**：创建/删除（作者或 admin 可删）
- **标签**：自动创建、列表查询

## 统一响应格式

所有接口返回统一 JSON 格式：

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

错误响应：

```json
{
  "code": 404,
  "message": "文章不存在",
  "data": null
}
```

## 全局异常处理

| 异常类型 | HTTP 状态码 | 说明 |
|----------|-------------|------|
| AppException | 400 | 业务异常基类 |
| NotFoundException | 404 | 资源不存在 |
| AuthenticationException | 401 | 认证失败 |
| PermissionDeniedException | 403 | 权限不足 |
| ConflictException | 409 | 资源冲突 |
| ValidationException | 422 | 业务校验失败 |
| RequestValidationError | 422 | Pydantic 参数校验 |
| Exception | 500 | 兜底未捕获异常 |

## 运行测试

```bash
# 运行全部测试（使用内存 SQLite，无需外部数据库）
pytest

# 运行指定测试文件
pytest tests/test_auth.py -v

# 运行指定测试类
pytest tests/test_rbac.py::TestUserManagementRBAC -v
```

测试覆盖：
- 注册（成功/重复/参数校验）
- 登录（表单/JSON/邮箱/错误密码/不存在用户）
- Token 刷新（成功/无效）
- 当前用户（带Token/不带Token/无效Token）
- 文章 CRUD（创建/列表/详情/更新/删除）
- 分页/关键字搜索/标签筛选
- 评论创建/删除
- RBAC（admin 可管理/普通用户被拒/跨用户操作权限）

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| SECRET_KEY | change_me_... | JWT 签名密钥 |
| ALGORITHM | HS256 | JWT 算法 |
| ACCESS_TOKEN_EXPIRE_MINUTES | 30 | Access Token 有效期(分钟) |
| REFRESH_TOKEN_EXPIRE_DAYS | 7 | Refresh Token 有效期(天) |
| DATABASE_URL | sqlite:///./data/app.db | 数据库连接 |
| ADMIN_USERNAME | admin | 管理员用户名 |
| ADMIN_PASSWORD | change_me_... | 管理员密码 |
| CORS_ORIGINS | * | CORS 允许的源 |

## 已知限制

1. 使用 SQLite 作为默认数据库，生产环境建议替换为 PostgreSQL/MySQL
2. 使用 `@app.on_event("startup")` 启动事件（FastAPI 新版建议使用 lifespan，但当前版本仍兼容）
3. RBAC 权限粒度为角色级，未实现细粒度的 API 级权限控制
4. 日志文件按天轮转保留 7 天，长时间运行需关注磁盘空间
5. 未实现文件上传/图片处理功能

## 开发约束

- Python 3.10+ 兼容（使用 `from __future__ import annotations`）
- 禁用 3.11 独有语法（tomllib/except* 等）
- PEP-8 规范 + 中文注释
- 分层架构：api / core / db / models / schemas / services / utils
- 敏感配置全部从 .env 读取，禁止硬编码
