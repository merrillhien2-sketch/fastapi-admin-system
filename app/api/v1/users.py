"""用户管理路由 - 用户CRUD（RBAC：admin 可管理）

所有路由前缀: /api/v1/users
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from loguru import logger
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.database import get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.user import (
    UserCreate,
    UserListOut,
    UserOut,
    UserUpdate,
)
from app.services.user_service import (
    ROLE_ADMIN,
    delete_user,
    get_users_list,
    register_user,
    update_user,
)
from app.utils.pagination import paginate
from app.utils.response import success

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get(
    "",
    summary="获取用户列表（分页）",
    response_model=PageResponse[UserListOut],
    dependencies=[Depends(require_roles(ROLE_ADMIN))],
)
def list_users(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页条数"),
    db: Session = Depends(get_db),
):
    """获取用户分页列表（仅 admin 可访问）"""
    logger.info(f"查询用户列表: page={page}, page_size={page_size}")
    items, total = get_users_list(db, page=page, page_size=page_size)

    user_list = [UserListOut.model_validate(u).model_dump() for u in items]
    from math import ceil
    total_pages = ceil(total / page_size) if page_size > 0 else 0

    return success(
        data={
            "items": user_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        },
        message="获取成功",
    )


@router.post(
    "",
    summary="创建用户（admin）",
    response_model=dict,
    dependencies=[Depends(require_roles(ROLE_ADMIN))],
)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    """管理员创建用户（可指定角色后缀在 username 中，此处简化为创建普通 user）"""
    logger.info(f"管理员创建用户: username={user_in.username}")
    user = register_user(db, user_in)
    return success(
        data=UserOut.model_validate(user).model_dump(),
        message="创建成功",
    )


@router.get(
    "/{user_id}",
    summary="获取用户详情",
    response_model=dict,
    dependencies=[Depends(require_roles(ROLE_ADMIN))],
)
def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
):
    """获取指定用户详情（仅 admin）"""
    from app.services.user_service import get_user_by_id
    from app.utils.exceptions import NotFoundException

    user = get_user_by_id(db, user_id)
    if user is None:
        raise NotFoundException("用户不存在")

    return success(
        data=UserOut.model_validate(user).model_dump(),
        message="获取成功",
    )


@router.put(
    "/{user_id}",
    summary="更新用户",
    response_model=dict,
    dependencies=[Depends(require_roles(ROLE_ADMIN))],
)
def update_user_detail(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
):
    """更新用户信息（仅 admin）"""
    logger.info(f"更新用户: id={user_id}")
    user = update_user(db, user_id, user_in)
    return success(
        data=UserOut.model_validate(user).model_dump(),
        message="更新成功",
    )


@router.delete(
    "/{user_id}",
    summary="删除用户",
    response_model=dict,
    dependencies=[Depends(require_roles(ROLE_ADMIN))],
)
def delete_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
):
    """删除用户（仅 admin）"""
    logger.info(f"删除用户: id={user_id}")
    delete_user(db, user_id)
    return success(data=None, message="删除成功")
