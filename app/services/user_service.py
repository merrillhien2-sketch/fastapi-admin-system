"""用户业务服务层

封装用户相关的核心业务逻辑：
- 注册（含密码哈希、角色分配）
- 认证（用户名/邮箱 + 密码校验）
- 用户 CRUD
- 角色管理
- 初始化管理员账号
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.role import Role, user_role
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.exceptions import (
    ConflictException,
    NotFoundException,
    ValidationException,
)


# ==================== 角色常量 ====================

ROLE_ADMIN = "admin"
ROLE_EDITOR = "editor"
ROLE_USER = "user"

# 内置角色及其默认权限
DEFAULT_ROLES: dict[str, list[str]] = {
    ROLE_ADMIN: ["*"],  # admin 拥有全部权限
    ROLE_EDITOR: ["article:read", "article:create", "article:update", "article:delete", "comment:create"],
    ROLE_USER: ["article:read", "comment:create"],
}


# ==================== 角色服务 ====================

def get_or_create_role(db: Session, role_name: str, description: str = "") -> Role:
    """获取或创建角色"""
    role = db.execute(
        select(Role).where(Role.name == role_name)
    ).scalar_one_or_none()
    if role is None:
        role = Role(name=role_name, description=description)
        db.add(role)
        db.flush()
    return role


def init_default_roles(db: Session) -> None:
    """初始化默认角色（admin / editor / user）"""
    for role_name, permissions in DEFAULT_ROLES.items():
        role = get_or_create_role(db, role_name, description=f"内置角色: {role_name}")
        # 权限不存在才创建（避免重复）
        existing = {p.permission for p in role.permissions}
        for perm in permissions:
            if perm not in existing:
                from app.models.role import RolePermission
                role.permissions.append(RolePermission(permission=perm))
    db.commit()


def get_user_role_names(db: Session, user: User) -> list[str]:
    """获取用户的角色名称列表"""
    db.refresh(user)
    return [r.name for r in user.roles]


# ==================== 用户服务 ====================

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """通过用户名查询用户"""
    return db.execute(
        select(User).where(User.username == username)
    ).scalar_one_or_none()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """通过邮箱查询用户"""
    return db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """通过 ID 查询用户"""
    return db.get(User, user_id)


def authenticate_user(db: Session, login: str, password: str) -> User:
    """认证用户（支持用户名或邮箱登录）

    :raises ValidationException: 用户名或密码错误
    """
    # 支持用户名或邮箱登录
    user = db.execute(
        select(User).where(
            or_(User.username == login, User.email == login)
        )
    ).scalar_one_or_none()

    if user is None:
        raise ValidationException("用户名或密码错误")
    if not verify_password(password, user.hashed_password):
        raise ValidationException("用户名或密码错误")
    if not user.is_active:
        raise ValidationException("账号已被禁用")

    return user


def register_user(db: Session, user_in: UserCreate, role_name: str = ROLE_USER) -> User:
    """注册新用户

    :raises ConflictException: 用户名或邮箱已存在
    """
    # 检查用户名是否已存在
    if get_user_by_username(db, user_in.username) is not None:
        raise ConflictException("用户名已存在")

    # 检查邮箱是否已存在
    if get_user_by_email(db, user_in.email) is not None:
        raise ConflictException("邮箱已被注册")

    # 创建用户
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        is_active=True,
    )

    # 分配角色
    role = get_or_create_role(db, role_name, description=f"内置角色: {role_name}")
    user.roles.append(role)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_users_list(
    db: Session,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[User], int]:
    """获取用户分页列表"""
    from app.utils.pagination import paginate

    query = select(User).order_by(User.id.desc())
    result = paginate(db, query, page=page, page_size=page_size)
    return result.items, result.total


def update_user(db: Session, user_id: int, user_in: UserUpdate) -> User:
    """更新用户信息

    :raises NotFoundException: 用户不存在
    """
    user = get_user_by_id(db, user_id)
    if user is None:
        raise NotFoundException("用户不存在")

    if user_in.email is not None:
        # 检查邮箱是否被其他用户占用
        existing = get_user_by_email(db, user_in.email)
        if existing is not None and existing.id != user_id:
            raise ConflictException("邮箱已被其他用户使用")
        user.email = user_in.email

    if user_in.is_active is not None:
        user.is_active = user_in.is_active

    if user_in.role_names is not None:
        # 重新分配角色
        user.roles.clear()
        for rn in user_in.role_names:
            if rn not in DEFAULT_ROLES:
                raise ValidationException(f"角色 '{rn}' 不存在")
            role = get_or_create_role(db, rn)
            user.roles.append(role)

    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> None:
    """删除用户

    :raises NotFoundException: 用户不存在
    """
    user = get_user_by_id(db, user_id)
    if user is None:
        raise NotFoundException("用户不存在")
    db.delete(user)
    db.commit()


def init_admin_user(db: Session) -> None:
    """初始化管理员账号（应用启动时调用）

    如果 admin 账号不存在则创建，密码从环境变量读取。
    """
    from app.core.config import settings

    admin = get_user_by_username(db, settings.ADMIN_USERNAME)
    if admin is not None:
        # 已存在则跳过
        return

    # 确保默认角色已初始化
    init_default_roles(db)

    # 创建管理员用户
    admin_user = User(
        username=settings.ADMIN_USERNAME,
        email=f"{settings.ADMIN_USERNAME}@example.com",
        hashed_password=hash_password(settings.ADMIN_PASSWORD),
        is_active=True,
    )
    admin_role = db.execute(
        select(Role).where(Role.name == ROLE_ADMIN)
    ).scalar_one()
    admin_user.roles.append(admin_role)

    db.add(admin_user)
    db.commit()

    from loguru import logger
    logger.info(f"[初始化] 管理员账号已创建: {settings.ADMIN_USERNAME}")


def has_role(user: User, role_names: list[str]) -> bool:
    """检查用户是否拥有指定角色之一"""
    user_roles = {r.name for r in user.roles}
    return bool(user_roles & set(role_names))


def has_permission(db: Session, user: User, permission: str) -> bool:
    """检查用户是否拥有指定权限

    admin 角色拥有通配符权限 '*'，视为拥有全部权限。
    """
    for role in user.roles:
        for rp in role.permissions:
            if rp.permission == "*" or rp.permission == permission:
                return True
    return False
