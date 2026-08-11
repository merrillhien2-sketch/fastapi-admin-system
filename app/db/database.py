"""数据库引擎与会话管理

使用 SQLAlchemy 2.0 风格创建 engine 和 Session。
支持 SQLite（自动处理 check_same_thread）。
对于内存 SQLite（:memory:），使用 StaticPool 保证连接共享同一数据库。
"""
from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

# --- 确保 SQLite 文件数据库的目录存在 ---
if settings.DATABASE_URL.startswith("sqlite:///"):
    _db_path = settings.DATABASE_URL.replace("sqlite:///", "", 1)
    _db_dir = os.path.dirname(_db_path)
    if _db_dir:
        os.makedirs(_db_dir, exist_ok=True)

# --- 创建引擎 ---
# SQLite 需要 check_same_thread=False 以支持 FastAPI 多线程访问
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")
_is_memory = ":memory:" in settings.DATABASE_URL

_connect_args = (
    {"check_same_thread": False}
    if _is_sqlite
    else {}
)

if _is_memory:
    # 内存 SQLite 使用 StaticPool 保证多连接共享同一个内存库
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args=_connect_args,
        poolclass=StaticPool,
        echo=False,
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args=_connect_args,
        echo=False,
        pool_pre_ping=True,
    )

# --- 会话工厂 ---
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db():
    """FastAPI 依赖：获取数据库会话

    使用 yield 方式确保请求结束后自动关闭会话。
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
