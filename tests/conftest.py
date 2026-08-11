"""pytest 配置文件

使用内存 SQLite 数据库进行测试，每个测试函数独立隔离。
通过环境变量在导入应用前注入测试配置。
"""
from __future__ import annotations

import os

# --- 在导入应用前设置测试环境变量 ---
# 内存 SQLite + StaticPool 保证多连接共享同一数据库
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test_secret_key_for_unit_testing_only"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "TestAdmin@2024_NotReal"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.database import SessionLocal, engine, get_db
from app.main import app
from app.services.user_service import init_admin_user, init_default_roles


@pytest.fixture()
def client():
    """每个测试用例独立的测试客户端

    策略：
    1. 每个测试前 drop_all + create_all 重建表结构（测试隔离）
    2. 初始化默认角色和管理员账号
    3. 使用 TestClient 上下文管理器触发 startup 事件
    4. 测试后清理
    """
    # 重建表结构
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # 初始化默认角色和管理员
    db: Session = SessionLocal()
    try:
        init_default_roles(db)
        init_admin_user(db)
    finally:
        db.close()

    # 创建测试客户端
    with TestClient(app) as c:
        yield c

    # 测试后清理
    Base.metadata.drop_all(bind=engine)


# ==================== 测试辅助函数 ====================

def register_user(
    client: TestClient,
    username: str = "testuser",
    email: str = "test@example.com",
    password: str = "password123",
):
    """注册用户并返回响应"""
    return client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
        },
    )


def login_user(
    client: TestClient,
    username: str = "testuser",
    password: str = "password123",
):
    """登录用户并返回响应"""
    return client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )


def get_auth_headers(token: str) -> dict[str, str]:
    """构造 Authorization 请求头"""
    return {"Authorization": f"Bearer {token}"}


def register_and_get_token(
    client: TestClient,
    username: str = "testuser",
    email: str = "test@example.com",
    password: str = "password123",
) -> str:
    """注册用户并返回 access_token"""
    register_user(client, username, email, password)
    resp = login_user(client, username, password)
    return resp.json()["data"]["access_token"]


def login_admin(client: TestClient) -> str:
    """登录管理员并返回 access_token"""
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "TestAdmin@2024_NotReal"},
    )
    return resp.json()["data"]["access_token"]
