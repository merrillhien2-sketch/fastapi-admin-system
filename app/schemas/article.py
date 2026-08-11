"""文章相关 Schema - 文章/评论/标签
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ==================== 标签 ====================

class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="标签名称")

    @field_validator("name")
    @classmethod
    def name_stripped(cls, v: str) -> str:
        return v.strip()


class TagCreate(TagBase):
    pass


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime


# ==================== 评论 ====================

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000, description="评论内容")


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    article_id: int
    author_id: int
    author_name: str = Field(description="评论者用户名")
    created_at: datetime


# ==================== 文章 ====================

class ArticleBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="标题")
    content: str = Field(..., min_length=1, description="正文")
    summary: Optional[str] = Field(default=None, max_length=500, description="摘要")
    tag_names: List[str] = Field(default_factory=list, description="标签名称列表")


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(BaseModel):
    """文章更新（所有字段可选）"""
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content: Optional[str] = Field(default=None, min_length=1)
    summary: Optional[str] = Field(default=None, max_length=500)
    tag_names: Optional[List[str]] = None


class ArticleOut(BaseModel):
    """文章详情输出"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    summary: Optional[str] = None
    author_id: int
    author_name: str = Field(description="作者用户名")
    tags: List[str] = Field(default_factory=list, description="标签名称列表")
    comments: List[CommentOut] = Field(default_factory=list, description="评论列表")
    created_at: datetime
    updated_at: datetime


class ArticleListOut(BaseModel):
    """文章列表项输出（不含正文和评论，减少传输量）"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    summary: Optional[str] = None
    author_id: int
    author_name: str = Field(description="作者用户名")
    tags: List[str] = Field(default_factory=list, description="标签名称列表")
    comment_count: int = Field(default=0, description="评论数")
    created_at: datetime
    updated_at: datetime


class ArticleQueryParams(BaseModel):
    """文章查询参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页条数")
    keyword: Optional[str] = Field(default=None, description="标题/摘要关键字搜索")
    tag: Optional[str] = Field(default=None, description="按标签筛选")
