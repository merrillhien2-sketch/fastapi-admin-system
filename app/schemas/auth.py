"""认证相关 Schema - 注册/登录/Token
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=128, description="密码")

    @field_validator("username")
    @classmethod
    def username_no_space(cls, v: str) -> str:
        if " " in v:
            raise ValueError("用户名不能包含空格")
        return v.strip()


class LoginRequest(BaseModel):
    """用户登录请求（支持用户名或邮箱）"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str = Field(description="访问令牌")
    refresh_token: str = Field(description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str = Field(..., description="刷新令牌")


class TokenData(BaseModel):
    """Token 中解析出的数据"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
