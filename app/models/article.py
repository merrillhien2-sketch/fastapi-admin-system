"""文章模型

文章与用户（作者）多对一，与标签多对多，与评论一对多。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.tag import article_tag


class Article(Base):
    """文章表"""

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="文章 ID")
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True, comment="标题")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="正文")
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="摘要")

    # 作者（多对一）
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", back_populates="articles"
    )

    # 标签（多对多）
    tags: Mapped[list["Tag"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Tag",
        secondary=article_tag,
        back_populates="articles",
        lazy="selectin",
    )

    # 评论（一对多）
    comments: Mapped[list["Comment"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Comment",
        back_populates="article",
        cascade="all, delete-orphan",
        order_by="Comment.created_at.desc()",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    def __repr__(self) -> str:
        return f"<Article(id={self.id}, title={self.title})>"
