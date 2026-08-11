"""RBAC 权限控制测试

覆盖：
- admin 可访问用户管理接口
- 普通用户不能访问用户管理接口（403）
- 普通用户不能删除他人文章
- admin 可以删除任何文章
- 普通用户不能更新他人文章
- admin 可以更新任何文章
"""
from __future__ import annotations

from conftest import (
    get_auth_headers,
    login_admin,
    login_user,
    register_user,
)


# ==================== 辅助函数 ====================

def _register_and_login(
    client,
    username="rbacuser",
    email="rbac@example.com",
    password="password123",
) -> str:
    """注册并登录普通用户，返回 access_token"""
    register_user(client, username, email, password)
    resp = login_user(client, username, password)
    return resp.json()["data"]["access_token"]


def _create_article(client, token, title="RBAC测试文章"):
    """创建文章并返回文章 ID"""
    resp = client.post(
        "/api/v1/articles",
        json={"title": title, "content": "正文", "tag_names": []},
        headers=get_auth_headers(token),
    )
    return resp.json()["data"]["id"]


# ==================== 用户管理 RBAC 测试 ====================

class TestUserManagementRBAC:
    """用户管理接口的 RBAC 测试"""

    def test_admin_can_list_users(self, client):
        """admin 可以访问用户列表"""
        admin_token = login_admin(client)
        resp = client.get(
            "/api/v1/users",
            headers=get_auth_headers(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 1  # 至少有 admin 用户

    def test_normal_user_cannot_list_users(self, client):
        """普通用户不能访问用户列表（403）"""
        token = _register_and_login(client)
        resp = client.get(
            "/api/v1/users",
            headers=get_auth_headers(token),
        )
        assert resp.status_code == 403
        assert resp.json()["code"] == 403

    def test_normal_user_cannot_create_user(self, client):
        """普通用户不能创建用户（403）"""
        token = _register_and_login(client)
        resp = client.post(
            "/api/v1/users",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "password123",
            },
            headers=get_auth_headers(token),
        )
        assert resp.status_code == 403

    def test_normal_user_cannot_delete_user(self, client):
        """普通用户不能删除用户（403）"""
        token = _register_and_login(client)
        resp = client.delete(
            "/api/v1/users/1",
            headers=get_auth_headers(token),
        )
        assert resp.status_code == 403

    def test_admin_can_delete_user(self, client):
        """admin 可以删除用户"""
        admin_token = login_admin(client)
        # 先注册一个普通用户
        register_user(client, username="todelete", email="del@example.com")
        # 查找该用户 ID
        resp = client.get(
            "/api/v1/users",
            headers=get_auth_headers(admin_token),
        )
        users = resp.json()["data"]["items"]
        user_id = next(u["id"] for u in users if u["username"] == "todelete")

        # 删除用户
        resp = client.delete(
            f"/api/v1/users/{user_id}",
            headers=get_auth_headers(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "删除成功"

    def test_admin_can_update_user_roles(self, client):
        """admin 可以更新用户角色"""
        admin_token = login_admin(client)
        register_user(client, username="rolechange", email="role@example.com")

        # 查找用户 ID
        resp = client.get(
            "/api/v1/users",
            headers=get_auth_headers(admin_token),
        )
        users = resp.json()["data"]["items"]
        user_id = next(u["id"] for u in users if u["username"] == "rolechange")

        # 更新角色为 editor
        resp = client.put(
            f"/api/v1/users/{user_id}",
            json={"role_names": ["editor"]},
            headers=get_auth_headers(admin_token),
        )
        assert resp.status_code == 200
        roles = resp.json()["data"]["roles"]
        assert "editor" in roles
        assert "user" not in roles

    def test_no_token_cannot_access_users(self, client):
        """不带 Token 不能访问用户管理"""
        resp = client.get("/api/v1/users")
        assert resp.status_code == 401


# ==================== 文章 RBAC 测试 ====================

class TestArticleRBAC:
    """文章操作的 RBAC 测试"""

    def test_user_cannot_update_others_article(self, client):
        """普通用户不能修改他人文章（403）"""
        # 用户 A 创建文章
        token_a = _register_and_login(client, username="userA", email="a@example.com")
        article_id = _create_article(client, token_a, title="用户A的文章")

        # 用户 B 尝试修改
        token_b = _register_and_login(client, username="userB", email="b@example.com")
        resp = client.put(
            f"/api/v1/articles/{article_id}",
            json={"title": "被篡改的标题"},
            headers=get_auth_headers(token_b),
        )
        assert resp.status_code == 403
        assert resp.json()["message"] == "无权修改他人文章"

    def test_user_cannot_delete_others_article(self, client):
        """普通用户不能删除他人文章（403）"""
        token_a = _register_and_login(client, username="userA", email="a@example.com")
        article_id = _create_article(client, token_a, title="用户A的文章")

        token_b = _register_and_login(client, username="userB", email="b@example.com")
        resp = client.delete(
            f"/api/v1/articles/{article_id}",
            headers=get_auth_headers(token_b),
        )
        assert resp.status_code == 403
        assert resp.json()["message"] == "无权删除他人文章"

    def test_admin_can_delete_any_article(self, client):
        """admin 可以删除任何文章"""
        # 普通用户创建文章
        token = _register_and_login(client, username="author", email="auth@example.com")
        article_id = _create_article(client, token, title="普通用户的文章")

        # admin 删除该文章
        admin_token = login_admin(client)
        resp = client.delete(
            f"/api/v1/articles/{article_id}",
            headers=get_auth_headers(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "删除成功"

    def test_admin_can_update_any_article(self, client):
        """admin 可以修改任何文章"""
        token = _register_and_login(client, username="author", email="auth@example.com")
        article_id = _create_article(client, token, title="原标题")

        admin_token = login_admin(client)
        resp = client.put(
            f"/api/v1/articles/{article_id}",
            json={"title": "admin修改后的标题"},
            headers=get_auth_headers(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "admin修改后的标题"

    def test_user_can_update_own_article(self, client):
        """用户可以修改自己的文章"""
        token = _register_and_login(client)
        article_id = _create_article(client, token, title="自己的文章")

        resp = client.put(
            f"/api/v1/articles/{article_id}",
            json={"title": "修改后的标题"},
            headers=get_auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "修改后的标题"


# ==================== 评论 RBAC 测试 ====================

class TestCommentRBAC:
    """评论操作的 RBAC 测试"""

    def test_user_cannot_delete_others_comment(self, client):
        """普通用户不能删除他人评论（403）"""
        # 用户 A 创建文章和评论
        token_a = _register_and_login(client, username="userA", email="a@example.com")
        article_id = _create_article(client, token_a, title="评论RBAC文章")
        comment_resp = client.post(
            f"/api/v1/articles/{article_id}/comments",
            json={"content": "用户A的评论"},
            headers=get_auth_headers(token_a),
        )
        comment_id = comment_resp.json()["data"]["id"]

        # 用户 B 尝试删除评论
        token_b = _register_and_login(client, username="userB", email="b@example.com")
        resp = client.delete(
            f"/api/v1/articles/{article_id}/comments/{comment_id}",
            headers=get_auth_headers(token_b),
        )
        assert resp.status_code == 403

    def test_admin_can_delete_any_comment(self, client):
        """admin 可以删除任何评论"""
        token = _register_and_login(client, username="author", email="auth@example.com")
        article_id = _create_article(client, token, title="文章")
        comment_resp = client.post(
            f"/api/v1/articles/{article_id}/comments",
            json={"content": "评论内容"},
            headers=get_auth_headers(token),
        )
        comment_id = comment_resp.json()["data"]["id"]

        admin_token = login_admin(client)
        resp = client.delete(
            f"/api/v1/articles/{article_id}/comments/{comment_id}",
            headers=get_auth_headers(admin_token),
        )
        assert resp.status_code == 200
