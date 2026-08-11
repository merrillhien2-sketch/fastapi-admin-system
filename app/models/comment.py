"""评论模型

评论与文章（多对一），与用户（多对一）。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Comment(Base):
    """评论表"""

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="评论 ID")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="评论内容")

    # 所属文章（多对一）
    article_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    article: Mapped["Article"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Article", back_populates="comments"
    )

    # 评论作者（多对一）
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", back_populates="comments"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="创建时间"
    )

    def __repr__(self) -> str:
        return f"<Comment(id={self.id}, article_id={self.article_id})>"
