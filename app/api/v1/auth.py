"""认证路由 - 注册/登录/刷新Token/当前用户

所有路由前缀: /api/v1/auth
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from loguru import logger
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.common import ResponseModel
from app.schemas.user import UserOut
from app.services.user_service import authenticate_user, register_user
from app.utils.response import success

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", summary="用户注册", response_model=ResponseModel[UserOut])
def register(
    user_in: RegisterRequest,
    db: Session = Depends(get_db),
):
    """用户注册（默认角色为 user）"""
    logger.info(f"注册请求: username={user_in.username}")
    user = register_user(db, user_in)
    return success(
        data=UserOut.model_validate(user).model_dump(),
        message="注册成功",
    )


@router.post("/login", summary="用户登录", response_model=ResponseModel[TokenResponse])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """用户登录（OAuth2 密码模式）

    使用表单提交 username + password，返回 access_token 和 refresh_token。
    兼容 Swagger Authorize 按钮直接登录。
    """
    logger.info(f"登录请求(OAuth2表单): username={form_data.username}")
    user = authenticate_user(db, form_data.username, form_data.password)

    # 签发 token
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    return success(
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        ).model_dump(),
        message="登录成功",
    )


@router.post("/login/json", summary="用户登录(JSON)", response_model=ResponseModel[TokenResponse])
def login_json(
    login_in: LoginRequest,
    db: Session = Depends(get_db),
):
    """用户登录（JSON 方式，支持用户名或邮箱）"""
    logger.info(f"登录请求(JSON): username={login_in.username}")
    user = authenticate_user(db, login_in.username, login_in.password)

    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    return success(
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        ).model_dump(),
        message="登录成功",
    )


@router.post("/refresh", summary="刷新Token", response_model=ResponseModel[TokenResponse])
def refresh_token(
    refresh_in: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """使用 refresh_token 刷新 access_token"""
    user_id = verify_refresh_token(refresh_in.refresh_token)
    if user_id is None:
        from app.utils.exceptions import AuthenticationException
        raise AuthenticationException("无效或过期的刷新令牌")

    # 签发新的 access token
    new_access_token = create_access_token(subject=user_id)
    new_refresh_token = create_refresh_token(subject=user_id)

    return success(
        data=TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        ).model_dump(),
        message="刷新成功",
    )


@router.get("/me", summary="获取当前用户信息", response_model=ResponseModel[UserOut])
def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户的详细信息"""
    return success(
        data=UserOut.model_validate(current_user).model_dump(),
        message="获取成功",
    )
