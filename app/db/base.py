"""数据库基类定义

使用 SQLAlchemy 2.0 的 DeclarativeBase 作为所有 ORM 模型的基类。
"""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """所有 ORM 模型的声明式基类"""
    pass
