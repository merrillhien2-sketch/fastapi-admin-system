"""安全模块 - JWT 生成/校验 + 密码哈希(bcrypt)

负责：
1. 使用 passlib[bcrypt] 对密码进行哈希与校验
2. 使用 python-jose 生成与校验 JWT access/refresh token
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# --- 密码哈希上下文 ---
# 使用 bcrypt 算法对密码进行哈希
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==================== 密码工具函数 ====================

def hash_password(password: str) -> str:
    """对明文密码进行 bcrypt 哈希"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与哈希密码是否匹配"""
    return pwd_context.verify(plain_password, hashed_password)


# ==================== JWT 工具函数 ====================

def create_access_token(
    subject: str | int,
    extra_claims: Optional[dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """生成 Access Token

    :param subject: JWT 主题（通常为用户 ID 字符串）
    :param extra_claims: 额外声明（如角色列表）
    :param expires_delta: 自定义过期时间，默认取配置
    :return: 编码后的 JWT 字符串
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
    }
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(
    subject: str | int,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """生成 Refresh Token（用于刷新 access token）"""
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """解码并验证 JWT

    :raises JWTError: token 无效或已过期时抛出
    :return: 解码后的 payload 字典
    """
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    return payload


def verify_access_token(token: str) -> Optional[str]:
    """验证 access token，返回用户 ID（sub），失败返回 None"""
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        sub: Optional[str] = payload.get("sub")
        return sub
    except JWTError:
        return None


def verify_refresh_token(token: str) -> Optional[str]:
    """验证 refresh token，返回用户 ID（sub），失败返回 None"""
    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            return None
        sub: Optional[str] = payload.get("sub")
        return sub
    except JWTError:
        return None
