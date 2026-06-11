@echo off
chcp 65001 >nul
echo ========================================
echo   3D照片生成器 - 一键安装
echo ========================================
echo.

cd /d D:\3d-photo

:: 使用系统Python
echo [1/2] 创建虚拟环境...
if not exist venv\Scripts\python.exe (
    python -m venv venv
)

call venv\Scripts\activate.bat

echo [2/2] 安装依赖...
pip install fastapi uvicorn python-multipart requests pillow -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo ========================================
echo   ✅ 安装完成！运行 start.bat 启动
echo ========================================
pause
