"""自定义异常与全局异常处理

业务异常体系：
- AppException: 所有自定义业务异常的基类
  - NotFoundException: 资源不存在 (404)
  - AuthenticationException: 认证失败 (401)
  - PermissionDeniedException: 权限不足 (403)
  - ConflictException: 资源冲突 (409)
  - ValidationException: 业务校验失败 (422)

全局异常处理器注册在 register_exception_handlers() 中，
捕获以下异常并返回统一格式 {code, message, data}：
1. AppException 及其子类
2. HTTPException（FastAPI 内置）
3. RequestValidationError（Pydantic 参数校验）
4. Exception（500 兜底）
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException


# ==================== 自定义异常 ====================

class AppException(Exception):
    """业务异常基类

    :param message: 异常消息
    :param code: 业务状态码
    :param status_code: HTTP 状态码
    :param data: 附加数据
    """

    def __init__(
        self,
        message: str = "业务异常",
        code: int = 400,
        status_code: int = 400,
        data: Optional[Any] = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.data = data
        super().__init__(message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code}, message={self.message})"


class NotFoundException(AppException):
    """资源不存在"""

    def __init__(self, message: str = "资源不存在", data: Optional[Any] = None) -> None:
        super().__init__(message=message, code=404, status_code=404, data=data)


class AuthenticationException(AppException):
    """认证失败（未登录或 token 无效）"""

    def __init__(self, message: str = "认证失败", data: Optional[Any] = None) -> None:
        super().__init__(message=message, code=401, status_code=401, data=data)


class PermissionDeniedException(AppException):
    """权限不足"""

    def __init__(self, message: str = "权限不足", data: Optional[Any] = None) -> None:
        super().__init__(message=message, code=403, status_code=403, data=data)


class ConflictException(AppException):
    """资源冲突（如用户名已存在）"""

    def __init__(self, message: str = "资源冲突", data: Optional[Any] = None) -> None:
        super().__init__(message=message, code=409, status_code=409, data=data)


class ValidationException(AppException):
    """业务校验失败"""

    def __init__(self, message: str = "参数校验失败", data: Optional[Any] = None) -> None:
        super().__init__(message=message, code=422, status_code=422, data=data)


# ==================== 全局异常处理器注册 ====================

def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器到 FastAPI 应用"""

    # --- 1. 业务异常 ---
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            f"业务异常 [{request.method} {request.url.path}] "
            f"code={exc.code} message={exc.message}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message, "data": exc.data},
        )

    # --- 2. FastAPI HTTPException ---
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        logger.warning(
            f"HTTP 异常 [{request.method} {request.url.path}] "
            f"status={exc.status_code} detail={exc.detail}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.status_code, "message": str(exc.detail), "data": None},
        )

    # --- 3. Starlette HTTPException（兜底 FastAPI 未捕获的） ---
    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        logger.warning(
            f"Starlette HTTP 异常 [{request.method} {request.url.path}] "
            f"status={exc.status_code} detail={exc.detail}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.status_code, "message": str(exc.detail), "data": None},
        )

    # --- 4. Pydantic 请求参数校验异常 ---
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning(
            f"参数校验失败 [{request.method} {request.url.path}] errors={exc.errors()}"
        )
        # 使用 jsonable_encoder 处理可能包含 ValueError 等不可序列化对象的错误数据
        from fastapi.encoders import jsonable_encoder
        return JSONResponse(
            status_code=422,
            content={
                "code": 422,
                "message": "参数校验失败",
                "data": jsonable_encoder(exc.errors()),
            },
        )

    # --- 5. 兜底：未捕获的异常 ---
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            f"未捕获异常 [{request.method} {request.url.path}] {exc}"
        )
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": "服务器内部错误",
                "data": None,
            },
        )
