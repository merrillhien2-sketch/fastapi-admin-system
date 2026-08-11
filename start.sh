#!/usr/bin/env bash
# ===== FastAPI 通用后台管理系统 - 一键启动脚本 (Linux/macOS) =====
set -e

echo "===== FastAPI 通用后台管理系统 启动脚本 ====="

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 检查 uv 是否可用
if command -v uv &> /dev/null; then
    echo "[1/3] 使用 uv 创建虚拟环境..."
    uv venv
    echo "[2/3] 使用 uv 安装依赖..."
    uv pip install -r requirements.txt
else
    echo "[1/3] uv 未找到，使用 python venv..."
    python3 -m venv venv
    source venv/bin/activate
    echo "[2/3] 安装依赖..."
    pip install -r requirements.txt
fi

# 创建数据与日志目录
mkdir -p data logs

echo "[3/3] 启动 uvicorn 服务..."
echo "访问地址: http://127.0.0.1:8000/docs"
echo "按 Ctrl+C 停止服务"
echo "============================================"

# 启动 uvicorn
if command -v uv &> /dev/null; then
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi
