"""分页工具

封装通用的分页查询逻辑，支持 SQLAlchemy 2.0 select 语句。
"""
from __future__ import annotations

from math import ceil
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.schemas.common import PageData


def paginate(
    db: Session,
    query: select,
    page: int = 1,
    page_size: int = 10,
) -> PageData:
    """执行分页查询

    :param db: 数据库会话
    :param query: SQLAlchemy select 查询语句（不含分页）
    :param page: 页码（从 1 开始）
    :param page_size: 每页条数
    :return: PageData 分页数据
    """
    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar() or 0

    # 计算分页参数
    offset = (page - 1) * page_size
    total_pages = ceil(total / page_size) if page_size > 0 else 0

    # 执行分页查询
    items = db.execute(
        query.offset(offset).limit(page_size)
    ).scalars().all()

    return PageData(
        items=list(items),
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
