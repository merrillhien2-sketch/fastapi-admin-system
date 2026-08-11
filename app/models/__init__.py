"""models 模块 - ORM 模型定义

导入所有模型以便 create_all 能正确创建全部表。
"""
from __future__ import annotations

from app.models.role import Role, RolePermission, user_role
from app.models.user import User
from app.models.tag import Tag, article_tag
from app.models.article import Article
from app.models.comment import Comment

__all__ = [
    "User",
    "Role",
    "RolePermission",
    "user_role",
    "Tag",
    "article_tag",
    "Article",
    "Comment",
]
