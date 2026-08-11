"""通用 Schema - 统一响应格式与分页

统一响应格式：{ "code": 200, "message": "success", "data": <T> }
"""
from __future__ import annotations

from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

# 泛型类型变量
T = TypeVar("T")


class ResponseBase(BaseModel):
    """统一响应基类"""
    code: int = Field(default=200, description="业务状态码")
    message: str = Field(default="success", description="提示消息")


class ResponseModel(ResponseBase, Generic[T]):
    """统一响应模型（带泛型 data）"""
    data: Optional[T] = Field(default=None, description="响应数据")


class PaginationParams(BaseModel):
    """分页查询参数"""
    page: int = Field(default=1, ge=1, description="页码，从 1 开始")
    page_size: int = Field(default=10, ge=1, le=100, description="每页条数")


class PageData(BaseModel, Generic[T]):
    """分页数据"""
    items: List[T] = Field(description="当前页数据列表")
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页条数")
    total_pages: int = Field(description="总页数")


class PageResponse(ResponseBase, Generic[T]):
    """分页统一响应"""
    data: Optional[PageData[T]] = Field(default=None, description="分页数据")


def build_response(
    data: Any = None,
    message: str = "success",
    code: int = 200,
) -> dict[str, Any]:
    """构建统一响应字典"""
    return {"code": code, "message": message, "data": data}
