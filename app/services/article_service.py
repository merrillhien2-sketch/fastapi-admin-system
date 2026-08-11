"""文章业务服务层

封装文章/评论/标签相关的核心业务逻辑：
- 文章 CRUD（含分页、关键字搜索、标签筛选）
- 标签 CRUD
- 评论 CRUD
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.article import Article
from app.models.comment import Comment
from app.models.tag import Tag, article_tag
from app.models.user import User
from app.schemas.article import (
    ArticleCreate,
    ArticleUpdate,
    CommentCreate,
    TagCreate,
)
from app.utils.exceptions import (
    NotFoundException,
    PermissionDeniedException,
)
from app.utils.pagination import paginate


# ==================== 标签服务 ====================

def get_or_create_tag(db: Session, tag_name: str) -> Tag:
    """获取或创建标签"""
    tag = db.execute(
        select(Tag).where(Tag.name == tag_name)
    ).scalar_one_or_none()
    if tag is None:
        tag = Tag(name=tag_name)
        db.add(tag)
        db.flush()
    return tag


def get_tags_list(db: Session) -> list[Tag]:
    """获取全部标签列表"""
    return list(db.execute(select(Tag).order_by(Tag.name)).scalars().all())


# ==================== 文章服务 ====================

def get_article_by_id(db: Session, article_id: int) -> Optional[Article]:
    """通过 ID 获取文章"""
    return db.get(Article, article_id)


def create_article(db: Session, article_in: ArticleCreate, author: User) -> Article:
    """创建文章"""
    article = Article(
        title=article_in.title,
        content=article_in.content,
        summary=article_in.summary,
        author_id=author.id,
    )
    # 先将文章加入会话，再处理标签关联（避免 SAWarning）
    db.add(article)

    # 处理标签
    for tag_name in article_in.tag_names:
        tag = get_or_create_tag(db, tag_name.strip())
        article.tags.append(tag)

    db.commit()
    db.refresh(article)
    return article


def get_articles_list(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    keyword: Optional[str] = None,
    tag: Optional[str] = None,
) -> tuple[list[Article], int]:
    """获取文章分页列表

    :param keyword: 标题/摘要关键字搜索
    :param tag: 按标签名称筛选
    """
    query = select(Article).order_by(Article.id.desc())

    # 关键字搜索（标题或摘要）
    if keyword:
        keyword_pattern = f"%{keyword}%"
        query = query.where(
            or_(
                Article.title.ilike(keyword_pattern),
                Article.summary.ilike(keyword_pattern),
            )
        )

    # 按标签筛选
    if tag:
        query = query.join(Article.tags).where(Tag.name == tag)

    result = paginate(db, query, page=page, page_size=page_size)
    return result.items, result.total


def update_article(
    db: Session, article_id: int, article_in: ArticleUpdate, current_user: User
) -> Article:
    """更新文章

    仅作者本人或 admin/editor 可修改。
    """
    article = get_article_by_id(db, article_id)
    if article is None:
        raise NotFoundException("文章不存在")

    # 权限校验：作者本人或 admin/editor
    from app.services.user_service import ROLE_ADMIN, ROLE_EDITOR, has_role
    is_author = article.author_id == current_user.id
    is_admin_or_editor = has_role(current_user, [ROLE_ADMIN, ROLE_EDITOR])
    if not (is_author or is_admin_or_editor):
        raise PermissionDeniedException("无权修改他人文章")

    if article_in.title is not None:
        article.title = article_in.title
    if article_in.content is not None:
        article.content = article_in.content
    if article_in.summary is not None:
        article.summary = article_in.summary
    if article_in.tag_names is not None:
        # 重新设置标签
        article.tags.clear()
        for tag_name in article_in.tag_names:
            t = get_or_create_tag(db, tag_name.strip())
            article.tags.append(t)

    db.commit()
    db.refresh(article)
    return article


def delete_article(db: Session, article_id: int, current_user: User) -> None:
    """删除文章

    仅作者本人或 admin 可删除。
    """
    article = get_article_by_id(db, article_id)
    if article is None:
        raise NotFoundException("文章不存在")

    from app.services.user_service import ROLE_ADMIN, has_role
    is_author = article.author_id == current_user.id
    is_admin = has_role(current_user, [ROLE_ADMIN])
    if not (is_author or is_admin):
        raise PermissionDeniedException("无权删除他人文章")

    db.delete(article)
    db.commit()


# ==================== 评论服务 ====================

def create_comment(
    db: Session, article_id: int, comment_in: CommentCreate, author: User
) -> Comment:
    """创建评论"""
    article = get_article_by_id(db, article_id)
    if article is None:
        raise NotFoundException("文章不存在")

    comment = Comment(
        content=comment_in.content,
        article_id=article_id,
        author_id=author.id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def get_comment_by_id(db: Session, comment_id: int) -> Optional[Comment]:
    """通过 ID 获取评论"""
    return db.get(Comment, comment_id)


def delete_comment(db: Session, comment_id: int, current_user: User) -> None:
    """删除评论

    仅评论作者或 admin 可删除。
    """
    comment = get_comment_by_id(db, comment_id)
    if comment is None:
        raise NotFoundException("评论不存在")

    from app.services.user_service import ROLE_ADMIN, has_role
    is_author = comment.author_id == current_user.id
    is_admin = has_role(current_user, [ROLE_ADMIN])
    if not (is_author or is_admin):
        raise PermissionDeniedException("无权删除他人评论")

    db.delete(comment)
    db.commit()
