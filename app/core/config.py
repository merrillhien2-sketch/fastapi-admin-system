"""全局配置模块

使用 pydantic-settings 从 .env 文件读取环境变量，禁止硬编码密钥。
所有敏感配置均从环境变量注入。
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类，从 .env 文件自动加载"""

    # --- 应用基本配置 ---
    APP_NAME: str = "FastAPI Admin System"

    # --- JWT 安全配置 ---
    SECRET_KEY: str = "change_me_to_a_random_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- 数据库配置 ---
    DATABASE_URL: str = "sqlite:///./data/app.db"

    # --- 初始管理员配置 ---
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "change_me_to_a_strong_password"

    # --- CORS 配置 ---
    CORS_ORIGINS: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_not_be_empty(cls, v: str) -> str:
        """校验密钥不能为空"""
        if not v or not v.strip():
            raise ValueError("SECRET_KEY 不能为空")
        return v

    @property
    def cors_origin_list(self) -> List[str]:
        """将 CORS_ORIGINS 字符串转为列表"""
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    """获取配置单例（带缓存，避免重复读取 .env）"""
    return Settings()


# 全局配置实例
settings = get_settings()
