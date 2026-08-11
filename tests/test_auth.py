"""认证模块测试

覆盖：
- 用户注册（成功/重复/参数校验）
- 用户登录（OAuth2表单/JSON/错误密码/禁用账号）
- 刷新 Token
- 获取当前用户信息（带Token/不带Token）
"""
from __future__ import annotations

from conftest import (
    get_auth_headers,
    login_admin,
    login_user,
    register_user,
)


# ==================== 注册测试 ====================

class TestRegister:
    """用户注册测试"""

    def test_register_success(self, client):
        """注册成功"""
        resp = register_user(client)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200
        assert data["message"] == "注册成功"
        assert data["data"]["username"] == "testuser"
        assert data["data"]["email"] == "test@example.com"
        assert "password" not in str(data["data"])
        assert "hashed_password" not in str(data["data"])
        # 默认角色应为 user
        assert "user" in data["data"]["roles"]

    def test_register_duplicate_username(self, client):
        """重复用户名注册失败"""
        register_user(client, username="dupuser", email="user1@example.com")
        resp = register_user(
            client, username="dupuser", email="user2@example.com"
        )
        assert resp.status_code == 409
        assert resp.json()["message"] == "用户名已存在"

    def test_register_duplicate_email(self, client):
        """重复邮箱注册失败"""
        register_user(client, username="user1", email="dup@example.com")
        resp = register_user(
            client, username="user2", email="dup@example.com"
        )
        assert resp.status_code == 409
        assert resp.json()["message"] == "邮箱已被注册"

    def test_register_short_password(self, client):
        """密码过短校验失败"""
        resp = register_user(
            client, username="shortpw", email="short@example.com", password="123"
        )
        assert resp.status_code == 422
        assert resp.json()["code"] == 422

    def test_register_invalid_email(self, client):
        """邮箱格式校验失败"""
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "username": "bademail",
                "email": "not-an-email",
                "password": "password123",
            },
        )
        assert resp.status_code == 422

    def test_register_username_with_space(self, client):
        """用户名包含空格校验失败"""
        resp = register_user(
            client, username="has space", email="space@example.com"
        )
        assert resp.status_code == 422


# ==================== 登录测试 ====================

class TestLogin:
    """用户登录测试"""

    def test_login_oauth2_form(self, client):
        """OAuth2 表单登录成功"""
        register_user(client)
        resp = login_user(client)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_json(self, client):
        """JSON 方式登录成功"""
        register_user(client)
        resp = client.post(
            "/api/v1/auth/login/json",
            json={"username": "testuser", "password": "password123"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()["data"]

    def test_login_with_email(self, client):
        """使用邮箱登录成功"""
        register_user(client)
        resp = client.post(
            "/api/v1/auth/login/json",
            json={"username": "test@example.com", "password": "password123"},
        )
        assert resp.status_code == 200

    def test_login_wrong_password(self, client):
        """错误密码登录失败"""
        register_user(client)
        resp = login_user(client, password="wrongpassword")
        assert resp.status_code == 422
        assert resp.json()["message"] == "用户名或密码错误"

    def test_login_nonexistent_user(self, client):
        """不存在的用户登录失败"""
        resp = login_user(client, username="nouser")
        assert resp.status_code == 422
        assert resp.json()["message"] == "用户名或密码错误"

    def test_admin_login(self, client):
        """管理员登录成功"""
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "TestAdmin@2024_NotReal"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "access_token" in data


# ==================== Token 刷新测试 ====================

class TestRefreshToken:
    """刷新 Token 测试"""

    def test_refresh_token_success(self, client):
        """刷新 Token 成功"""
        register_user(client)
        login_resp = login_user(client)
        refresh_token = login_resp.json()["data"]["refresh_token"]

        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_token_invalid(self, client):
        """无效刷新令牌失败"""
        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token_string"},
        )
        assert resp.status_code == 401
        assert resp.json()["message"] == "无效或过期的刷新令牌"


# ==================== 当前用户测试 ====================

class TestCurrentUser:
    """获取当前用户信息测试"""

    def test_get_me_success(self, client):
        """带 Token 获取当前用户信息"""
        token = register_and_login(client)
        resp = client.get("/api/v1/auth/me", headers=get_auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    def test_get_me_without_token(self, client):
        """不带 Token 获取当前用户信息失败"""
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401
        assert resp.json()["message"] in ("Not authenticated", "无效或过期的访问令牌")

    def test_get_me_invalid_token(self, client):
        """无效 Token 获取当前用户信息失败"""
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert resp.status_code == 401


# ==================== 辅助函数 ====================

def register_and_login(
    client,
    username="testuser",
    email="test@example.com",
    password="password123",
) -> str:
    """注册并登录，返回 access_token"""
    register_user(client, username, email, password)
    resp = login_user(client, username, password)
    return resp.json()["data"]["access_token"]
