"""文章模块测试

覆盖：
- 文章创建（带/不带鉴权）
- 文章列表（分页/关键字搜索/标签筛选）
- 文章详情
- 文章更新（作者/admin/editor 权限）
- 文章删除
- 评论创建/删除
- 标签列表
"""
from __future__ import annotations

from conftest import (
    get_auth_headers,
    login_admin,
    login_user,
    register_user,
)


# ==================== 辅助函数 ====================

def _create_article(
    client,
    token,
    title="测试文章标题",
    content="这是测试文章的正文内容。",
    summary="测试摘要",
    tags=None,
):
    """创建文章辅助函数"""
    body = {
        "title": title,
        "content": content,
        "summary": summary,
        "tag_names": tags or [],
    }
    return client.post(
        "/api/v1/articles",
        json=body,
        headers=get_auth_headers(token),
    )


def _register_and_login(
    client,
    username="articleuser",
    email="article@example.com",
    password="password123",
) -> str:
    """注册并登录，返回 access_token"""
    register_user(client, username, email, password)
    resp = login_user(client, username, password)
    return resp.json()["data"]["access_token"]


# ==================== 文章 CRUD 测试 ====================

class TestArticleCRUD:
    """文章增删改查测试"""

    def test_create_article_success(self, client):
        """创建文章成功"""
        token = _register_and_login(client)
        resp = _create_article(client, token, tags=["Python", "FastAPI"])
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["title"] == "测试文章标题"
        assert data["content"] == "这是测试文章的正文内容。"
        assert "Python" in data["tags"]
        assert "FastAPI" in data["tags"]
        assert data["author_name"] == "articleuser"

    def test_create_article_without_auth(self, client):
        """未登录创建文章失败"""
        resp = client.post(
            "/api/v1/articles",
            json={
                "title": "无权限文章",
                "content": "内容",
                "tag_names": [],
            },
        )
        assert resp.status_code == 401

    def test_create_article_validation_error(self, client):
        """创建文章参数校验失败（标题为空）"""
        token = _register_and_login(client)
        resp = client.post(
            "/api/v1/articles",
            json={"title": "", "content": "内容", "tag_names": []},
            headers=get_auth_headers(token),
        )
        assert resp.status_code == 422

    def test_get_article_list(self, client):
        """获取文章列表"""
        token = _register_and_login(client)
        # 创建 3 篇文章
        for i in range(3):
            _create_article(client, token, title=f"文章{i}")

        resp = client.get("/api/v1/articles")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 3
        assert len(data["items"]) == 3
        assert data["page"] == 1
        assert data["total_pages"] == 1

    def test_get_article_list_pagination(self, client):
        """文章列表分页"""
        token = _register_and_login(client)
        for i in range(5):
            _create_article(client, token, title=f"分页文章{i}")

        # 每页 2 条，取第 2 页
        resp = client.get("/api/v1/articles?page=2&page_size=2")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["page"] == 2
        assert data["page_size"] == 2
        assert data["total_pages"] == 3

    def test_search_by_keyword(self, client):
        """关键字搜索"""
        token = _register_and_login(client)
        _create_article(client, token, title="FastAPI入门教程", summary="学FastAPI")
        _create_article(client, token, title="Django入门教程", summary="学Django")

        resp = client.get("/api/v1/articles?keyword=FastAPI")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 1
        assert "FastAPI" in data["items"][0]["title"]

    def test_filter_by_tag(self, client):
        """标签筛选"""
        token = _register_and_login(client)
        _create_article(client, token, title="标签文章1", tags=["Python"])
        _create_article(client, token, title="标签文章2", tags=["Java"])

        resp = client.get("/api/v1/articles?tag=Python")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 1
        assert "Python" in data["items"][0]["tags"]

    def test_get_article_detail(self, client):
        """获取文章详情"""
        token = _register_and_login(client)
        create_resp = _create_article(client, token, title="详情测试")
        article_id = create_resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/articles/{article_id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == article_id
        assert data["title"] == "详情测试"
        assert data["content"] == "这是测试文章的正文内容。"

    def test_get_article_detail_not_found(self, client):
        """获取不存在的文章详情"""
        resp = client.get("/api/v1/articles/99999")
        assert resp.status_code == 404
        assert resp.json()["message"] == "文章不存在"

    def test_update_article_by_author(self, client):
        """作者更新自己的文章"""
        token = _register_and_login(client)
        create_resp = _create_article(client, token, title="原标题")
        article_id = create_resp.json()["data"]["id"]

        resp = client.put(
            f"/api/v1/articles/{article_id}",
            json={"title": "新标题", "content": "新内容"},
            headers=get_auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "新标题"

    def test_delete_article_by_author(self, client):
        """作者删除自己的文章"""
        token = _register_and_login(client)
        create_resp = _create_article(client, token, title="待删除")
        article_id = create_resp.json()["data"]["id"]

        resp = client.delete(
            f"/api/v1/articles/{article_id}",
            headers=get_auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "删除成功"

        # 确认已删除
        resp = client.get(f"/api/v1/articles/{article_id}")
        assert resp.status_code == 404


# ==================== 评论测试 ====================

class TestComment:
    """评论增删测试"""

    def test_create_comment_success(self, client):
        """创建评论成功"""
        token = _register_and_login(client)
        create_resp = _create_article(client, token, title="评论测试文章")
        article_id = create_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/articles/{article_id}/comments",
            json={"content": "这是一条评论"},
            headers=get_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["content"] == "这是一条评论"
        assert data["article_id"] == article_id
        assert data["author_name"] == "articleuser"

    def test_comment_on_nonexistent_article(self, client):
        """评论不存在的文章失败"""
        token = _register_and_login(client)
        resp = client.post(
            "/api/v1/articles/99999/comments",
            json={"content": "评论"},
            headers=get_auth_headers(token),
        )
        assert resp.status_code == 404

    def test_delete_comment_by_author(self, client):
        """作者删除自己的评论"""
        token = _register_and_login(client)
        create_resp = _create_article(client, token, title="评论删除测试")
        article_id = create_resp.json()["data"]["id"]

        comment_resp = client.post(
            f"/api/v1/articles/{article_id}/comments",
            json={"content": "待删除评论"},
            headers=get_auth_headers(token),
        )
        comment_id = comment_resp.json()["data"]["id"]

        resp = client.delete(
            f"/api/v1/articles/{article_id}/comments/{comment_id}",
            headers=get_auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "删除成功"


# ==================== 标签测试 ====================

class TestTags:
    """标签列表测试"""

    def test_list_tags(self, client):
        """获取标签列表"""
        token = _register_and_login(client)
        _create_article(client, token, title="标签测试", tags=["Python", "Web"])

        resp = client.get("/api/v1/articles/tags")
        assert resp.status_code == 200
        data = resp.json()["data"]
        tag_names = [t["name"] for t in data]
        assert "Python" in tag_names
        assert "Web" in tag_names

    def test_list_tags_empty(self, client):
        """无标签时返回空列表"""
        resp = client.get("/api/v1/articles/tags")
        assert resp.status_code == 200
        assert resp.json()["data"] == []
