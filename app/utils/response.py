"""统一响应工具

提供 success / error 快捷函数，返回统一格式字典：
{ "code": <int>, "message": <str>, "data": <Any> }
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def success(
    data: Any = None,
    message: str = "success",
    code: int = 200,
) -> dict[str, Any]:
    """成功响应"""
    return {"code": code, "message": message, "data": data}


def error(
    message: str = "error",
    code: int = 400,
    data: Optional[Any] = None,
    status_code: Optional[int] = None,
) -> JSONResponse:
    """错误响应（返回 JSONResponse 以支持自定义 HTTP 状态码）

    :param message: 错误消息
    :param code: 业务状态码
    :param data: 附加数据
    :param status_code: HTTP 状态码，默认与 code 对齐
    """
    http_status = status_code or _map_code_to_http(code)
    return JSONResponse(
        status_code=http_status,
        content={"code": code, "message": message, "data": data},
    )


def _map_code_to_http(code: int) -> int:
    """将业务码映射为 HTTP 状态码"""
    if 200 <= code < 300:
        return 200
    if code == 401:
        return 401
    if code == 403:
        return 403
    if code == 404:
        return 404
    if code == 409:
        return 409
    if code == 422:
        return 422
    if code >= 500:
        return 500
    return 400
