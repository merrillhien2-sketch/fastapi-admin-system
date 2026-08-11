"""角色模型与用户-角色关联表

实现 RBAC（基于角色的访问控制）：
- Role: 角色表（admin / editor / user）
- RolePermission: 角色权限表
- user_role: 用户与角色的多对多关联表
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# --- 用户-角色 多对多关联表 ---
user_role = Table(
    "user_role",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    comment="用户-角色关联表",
)


class Role(Base):
    """角色表"""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="角色 ID")
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True, comment="角色名称")
    description: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="角色描述")

    # 关联：角色下的权限
    permissions: Mapped[list[RolePermission]] = relationship(
        "RolePermission",
        back_populates="role",
        cascade="all, delete-orphan",
    )

    # 关联：该角色下的用户
    users: Mapped[list["User"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User",
        secondary=user_role,
        back_populates="roles",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="创建时间"
    )

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name})>"


class RolePermission(Base):
    """角色权限表

    每个 Role 可以有多个权限标识（如 article:create, user:delete 等）。
    """

    __tablename__ = "role_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    permission: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="权限标识，如 article:create"
    )

    role: Mapped[Role] = relationship("Role", back_populates="permissions")

    def __repr__(self) -> str:
        return f"<RolePermission(role_id={self.role_id}, perm={self.permission})>"
