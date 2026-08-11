"""用户模型

存储用户基本信息及密码哈希，通过 user_role 关联表实现 RBAC。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.role import user_role


class User(Base):
    """用户表"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="用户 ID")
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True, comment="用户名"
    )
    email: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True, comment="邮箱"
    )
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=False, comment="密码哈希")
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否启用"
    )

    # RBAC：用户与角色多对多
    roles: Mapped[list["Role"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Role",
        secondary=user_role,
        back_populates="users",
        lazy="selectin",
    )

    # 关联：用户发表的文章
    articles: Mapped[list["Article"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Article",
        back_populates="author",
        cascade="all, delete-orphan",
    )

    # 关联：用户发表的评论
    comments: Mapped[list["Comment"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Comment",
        back_populates="author",
        cascade="all, delete-orphan",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"
