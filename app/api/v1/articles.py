"""文章管理路由 - 文章CRUD + 评论 + 标签

所有路由前缀: /api/v1/articles
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from loguru import logger
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.article import (
    ArticleCreate,
    ArticleListOut,
    ArticleOut,
    ArticleUpdate,
    CommentCreate,
    CommentOut,
    TagOut,
)
from app.services.article_service import (
    create_article,
    create_comment,
    delete_article,
    delete_comment,
    get_article_by_id,
    get_articles_list,
    get_tags_list,
    update_article,
)
from app.utils.exceptions import NotFoundException
from app.utils.response import success

router = APIRouter(prefix="/articles", tags=["文章管理"])


# ==================== 文章 CRUD ====================

@router.get("", summary="获取文章列表（分页+搜索+标签筛选）")
def list_articles(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页条数"),
    keyword: str | None = Query(default=None, description="标题/摘要关键字"),
    tag: str | None = Query(default=None, description="按标签筛选"),
    db: Session = Depends(get_db),
):
    """获取文章分页列表，支持关键字搜索和标签筛选（公开接口）"""
    logger.info(f"查询文章列表: page={page}, keyword={keyword}, tag={tag}")
    items, total = get_articles_list(
        db, page=page, page_size=page_size, keyword=keyword, tag=tag
    )

    from math import ceil
    total_pages = ceil(total / page_size) if page_size > 0 else 0

    # 构建列表输出
    article_list = []
    for a in items:
        article_list.append({
            "id": a.id,
            "title": a.title,
            "summary": a.summary,
            "author_id": a.author_id,
            "author_name": a.author.username if a.author else "",
            "tags": [t.name for t in a.tags],
            "comment_count": len(a.comments) if a.comments else 0,
            "created_at": a.created_at,
            "updated_at": a.updated_at,
        })

    return success(
        data={
            "items": article_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        },
        message="获取成功",
    )


@router.get("/tags", summary="获取标签列表")
def list_tags(db: Session = Depends(get_db)):
    """获取全部标签列表（公开接口）"""
    tags = get_tags_list(db)
    return success(
        data=[TagOut.model_validate(t).model_dump() for t in tags],
        message="获取成功",
    )


@router.get("/{article_id}", summary="获取文章详情")
def get_article_detail(
    article_id: int,
    db: Session = Depends(get_db),
):
    """获取文章详情（公开接口）"""
    article = get_article_by_id(db, article_id)
    if article is None:
        raise NotFoundException("文章不存在")

    # 构建评论列表输出
    comments = []
    for c in (article.comments or []):
        comments.append({
            "id": c.id,
            "content": c.content,
            "article_id": c.article_id,
            "author_id": c.author_id,
            "author_name": c.author.username if c.author else "",
            "created_at": c.created_at,
        })

    return success(
        data={
            "id": article.id,
            "title": article.title,
            "content": article.content,
            "summary": article.summary,
            "author_id": article.author_id,
            "author_name": article.author.username if article.author else "",
            "tags": [t.name for t in article.tags],
            "comments": comments,
            "created_at": article.created_at,
            "updated_at": article.updated_at,
        },
        message="获取成功",
    )


@router.post("", summary="创建文章（需登录）")
def create_article_endpoint(
    article_in: ArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建文章（需登录）"""
    logger.info(f"创建文章: title={article_in.title}, author={current_user.username}")
    article = create_article(db, article_in, current_user)

    return success(
        data={
            "id": article.id,
            "title": article.title,
            "content": article.content,
            "summary": article.summary,
            "author_id": article.author_id,
            "author_name": article.author.username,
            "tags": [t.name for t in article.tags],
            "comments": [],
            "created_at": article.created_at,
            "updated_at": article.updated_at,
        },
        message="创建成功",
    )


@router.put("/{article_id}", summary="更新文章（需登录）")
def update_article_endpoint(
    article_id: int,
    article_in: ArticleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新文章（作者本人或 admin/editor）"""
    logger.info(f"更新文章: id={article_id}, user={current_user.username}")
    article = update_article(db, article_id, article_in, current_user)

    return success(
        data={
            "id": article.id,
            "title": article.title,
            "content": article.content,
            "summary": article.summary,
            "author_id": article.author_id,
            "author_name": article.author.username,
            "tags": [t.name for t in article.tags],
            "created_at": article.created_at,
            "updated_at": article.updated_at,
        },
        message="更新成功",
    )


@router.delete("/{article_id}", summary="删除文章（需登录）")
def delete_article_endpoint(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除文章（作者本人或 admin）"""
    logger.info(f"删除文章: id={article_id}, user={current_user.username}")
    delete_article(db, article_id, current_user)
    return success(data=None, message="删除成功")


# ==================== 评论 CRUD ====================

@router.post("/{article_id}/comments", summary="创建评论（需登录）")
def create_comment_endpoint(
    article_id: int,
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """为文章创建评论（需登录）"""
    logger.info(
        f"创建评论: article_id={article_id}, author={current_user.username}"
    )
    comment = create_comment(db, article_id, comment_in, current_user)

    return success(
        data={
            "id": comment.id,
            "content": comment.content,
            "article_id": comment.article_id,
            "author_id": comment.author_id,
            "author_name": comment.author.username,
            "created_at": comment.created_at,
        },
        message="评论成功",
    )


@router.delete(
    "/{article_id}/comments/{comment_id}",
    summary="删除评论（需登录）",
)
def delete_comment_endpoint(
    article_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除评论（评论作者或 admin）"""
    logger.info(
        f"删除评论: comment_id={comment_id}, user={current_user.username}"
    )
    delete_comment(db, comment_id, current_user)
    return success(data=None, message="删除成功")
