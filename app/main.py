"""FastAPI 应用入口

负责：
1. 创建 FastAPI 应用实例
2. 注册 CORS 中间件
3. 注册日志中间件（请求/响应日志）
4. 注册全局异常处理器
5. 注册 API 路由（v1 版本）
6. 应用启动时自动建表 + 初始化默认角色和管理员账号
"""
from __future__ import annotations

import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.articles import router as articles_router
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.base import Base
from app.db.database import engine
from app.utils.exceptions import register_exception_handlers

# --- 初始化日志 ---
setup_logging()


# ==================== 日志中间件 ====================

class LoggingMiddleware(BaseHTTPMiddleware):
    """请求/响应日志中间件

    记录每个请求的方法、路径、状态码和耗时。
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # 请求日志
        logger.info(
            f"请求: {request.method} {request.url.path}"
        )

        response = await call_next(request)

        # 响应日志
        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"响应: {request.method} {request.url.path} "
            f"status={response.status_code} "
            f"耗时={process_time:.2f}ms"
        )

        # 在响应头中添加处理耗时
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        return response


# ==================== 创建应用 ====================

def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用"""
    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "基于 FastAPI 的通用后台管理系统，包含用户管理、RBAC 权限控制、"
            "博客文章/评论/标签等功能。提供完整的 RESTful API。"
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- 日志中间件 ---
    app.add_middleware(LoggingMiddleware)

    # --- 注册异常处理器 ---
    register_exception_handlers(app)

    # --- 注册路由 ---
    from fastapi import APIRouter
    api_router = APIRouter(prefix="/api/v1")
    api_router.include_router(auth_router)
    api_router.include_router(users_router)
    api_router.include_router(articles_router)
    app.include_router(api_router)

    # --- 健康检查 ---
    @app.get("/health", tags=["系统"], summary="健康检查")
    async def health_check():
        """健康检查接口"""
        return {"code": 200, "message": "success", "data": {"status": "healthy"}}

    # --- 根路径 ---
    @app.get("/", tags=["系统"], summary="根路径")
    async def root():
        """根路径，返回欢迎信息和文档地址"""
        return {
            "code": 200,
            "message": "success",
            "data": {
                "app": settings.APP_NAME,
                "version": "1.0.0",
                "docs": "/docs",
            },
        }

    # --- 启动事件：建表 + 初始化 ---
    @app.on_event("startup")
    async def on_startup():
        """应用启动时执行"""
        logger.info("===== 应用启动中 =====")

        # 1. 自动建表
        logger.info("正在创建数据库表...")
        # 导入所有模型确保被注册
        import app.models  # noqa: F401
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建完成")

        # 2. 初始化默认角色和管理员账号
        from app.db.database import SessionLocal
        from app.services.user_service import init_admin_user, init_default_roles

        db = SessionLocal()
        try:
            init_default_roles(db)
            init_admin_user(db)
        finally:
            db.close()

        logger.info("===== 应用启动完成 =====")

    return app


# 全局应用实例
app = create_app()
