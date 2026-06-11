@echo off
chcp 65001 >nul
cd /d D:\3d-photo
set TRIPO_API_KEY=tsk_LYTWnjBgzlleIXbZ8gniN-f25yqiRjUxssOxo2ZJMY4
call venv\Scripts\activate.bat
echo.
echo ========================================
echo   3D Photo Generator
echo   http://localhost:8080
echo ========================================
echo.
uvicorn backend.app:app --host 0.0.0.0 --port 8080
