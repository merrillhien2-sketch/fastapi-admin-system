@echo off
REM ===== FastAPI 通用后台管理系统 - 一键启动脚本 (Windows) =====
setlocal

cd /d "%~dp0"

echo ===== FastAPI 通用后台管理系统 启动脚本 =====

REM 检查 uv 是否可用
where uv >nul 2>&1
if %errorlevel% equ 0 (
    echo [1/3] 使用 uv 创建虚拟环境...
    uv venv
    echo [2/3] 使用 uv 安装依赖...
    uv pip install -r requirements.txt
    echo [3/3] 启动 uvicorn 服务...
    echo 访问地址: http://127.0.0.1:8000/docs
    echo ============================================
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
) else (
    echo [1/3] uv 未找到，使用 python venv...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo [2/3] 安装依赖...
    pip install -r requirements.txt
    echo [3/3] 启动 uvicorn 服务...
    echo 访问地址: http://127.0.0.1:8000/docs
    echo ============================================
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
)

pause
