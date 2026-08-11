"""标签模型与文章-标签关联表

文章与标签为多对多关系。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# --- 文章-标签 多对多关联表 ---
article_tag = Table(
    "article_tag",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    comment="文章-标签关联表",
)


class Tag(Base):
    """标签表"""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="标签 ID")
    name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True, comment="标签名称"
    )

    # 关联：该标签下的文章
    articles: Mapped[list["Article"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Article",
        secondary=article_tag,
        back_populates="tags",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="创建时间"
    )

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name={self.name})>"
