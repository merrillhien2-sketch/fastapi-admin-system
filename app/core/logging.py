"""日志模块 - 基于 loguru 的日志配置

功能：
1. 控制台彩色输出
2. 文件落盘（logs/app.log 按天轮转，保留 7 天）
3. 全局异常捕获日志
"""
from __future__ import annotations

import os
import sys

from loguru import logger

# 日志目录
LOG_DIR = os.path.join(os.getcwd(), "logs")


def setup_logging() -> None:
    """初始化日志配置

    - 移除 loguru 默认 handler
    - 添加控制台 handler（DEBUG 级别，彩色输出）
    - 添加文件 handler（INFO 级别，按天轮转）
    """
    # 确保日志目录存在
    os.makedirs(LOG_DIR, exist_ok=True)

    # 清空默认配置
    logger.remove()

    # 控制台输出
    logger.add(
        sys.stdout,
        level="DEBUG",
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # 文件输出 - 按天轮转，保留 7 天
    logger.add(
        os.path.join(LOG_DIR, "app_{time:YYYY-MM-DD}.log"),
        level="INFO",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
            "{name}:{function}:{line} | {message}"
        ),
        rotation="00:00",      # 每天午夜轮转
        retention="7 days",    # 保留 7 天
        encoding="utf-8",
        backtrace=True,
        diagnose=True,
    )

    # 捕获未处理异常
    def _handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.opt(exception=(exc_type, exc_value, exc_traceback)).error(
            "未捕获的异常"
        )

    sys.excepthook = _handle_exception

    logger.info("日志系统初始化完成")
