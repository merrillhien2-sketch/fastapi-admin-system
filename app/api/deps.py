"""FastAPI 依赖注入

提供以下依赖：
- get_db: 数据库会话依赖
- get_current_user: 从 JWT 解析当前登录用户
- require_roles: RBAC 角色权限校验依赖工厂
"""
from __future__ import annotations

from typing import Callable

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from loguru import logger
from sqlalchemy.orm import Session

from app.core.security import verify_access_token
from app.db.database import get_db
from app.models.user import User
from app.services.user_service import get_user_by_id, has_role
from app.utils.exceptions import (
    AuthenticationException,
    PermissionDeniedException,
)

# OAuth2 密码模式 token 获取地址
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ==================== 依赖函数 ====================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """从 JWT 解析当前登录用户

    :raises AuthenticationException: token 无效或用户不存在
    """
    user_id = verify_access_token(token)
    if user_id is None:
        raise AuthenticationException("无效或过期的访问令牌")

    try:
        uid = int(user_id)
    except (ValueError, TypeError):
        raise AuthenticationException("无效的令牌主体")

    user = get_user_by_id(db, uid)
    if user is None:
        raise AuthenticationException("用户不存在")

    if not user.is_active:
        raise AuthenticationException("账号已被禁用")

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前活跃用户（额外校验 is_active）"""
    if not current_user.is_active:
        raise AuthenticationException("账号已被禁用")
    return current_user


def require_roles(*role_names: str) -> Callable:
    """RBAC 角色权限校验依赖工厂

    用法：
        @router.get("/users", dependencies=[Depends(require_roles("admin"))])
        def list_users(...): ...

    :param role_names: 允许的角色名称（满足其一即可）
    :return: FastAPI 依赖函数
    """

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if not has_role(current_user, list(role_names)):
            logger.warning(
                f"权限拒绝: 用户 {current_user.username} "
                f"需要角色 {role_names}，实际拥有 {[r.name for r in current_user.roles]}"
            )
            raise PermissionDeniedException(
                f"需要以下角色之一: {', '.join(role_names)}"
            )
        return current_user

    return role_checker


def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User | None:
    """可选的用户依赖（token 不存在或无效时返回 None，不抛异常）

    用于公开接口中可选的鉴权场景。
    """
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1]
    user_id = verify_access_token(token)
    if user_id is None:
        return None
    try:
        uid = int(user_id)
    except (ValueError, TypeError):
        return None
    return get_user_by_id(db, uid)
