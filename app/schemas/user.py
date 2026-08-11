"""用户相关 Schema
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RoleOut(BaseModel):
    """角色输出"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None


class UserBase(BaseModel):
    """用户基础信息"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """用户创建请求"""
    password: str = Field(..., min_length=6, max_length=128)

    @field_validator("username")
    @classmethod
    def username_no_space(cls, v: str) -> str:
        if " " in v:
            raise ValueError("用户名不能包含空格")
        return v.strip()


class UserUpdate(BaseModel):
    """用户更新请求"""
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    role_names: Optional[List[str]] = Field(default=None, description="角色名称列表")


def _extract_role_names(roles: list) -> list[str]:
    """从 Role 对象列表提取角色名称字符串列表

    兼容 ORM 对象和纯字符串两种输入。
    """
    if not isinstance(roles, list):
        return []
    result: list[str] = []
    for r in roles:
        if isinstance(r, str):
            result.append(r)
        elif hasattr(r, "name"):
            result.append(r.name)
        else:
            result.append(str(r))
    return result


class UserOut(BaseModel):
    """用户输出"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    is_active: bool
    roles: List[str] = Field(default_factory=list, description="角色名称列表")
    created_at: datetime
    updated_at: datetime

    @field_validator("roles", mode="before")
    @classmethod
    def normalize_roles(cls, v: list) -> list[str]:
        """将 Role 对象列表转换为角色名称字符串列表"""
        return _extract_role_names(v)


class UserListOut(BaseModel):
    """用户列表输出"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    is_active: bool
    roles: List[str] = Field(default_factory=list)
    created_at: datetime

    @field_validator("roles", mode="before")
    @classmethod
    def normalize_roles(cls, v: list) -> list[str]:
        """将 Role 对象列表转换为角色名称字符串列表"""
        return _extract_role_names(v)
