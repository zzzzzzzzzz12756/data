FROM python:3.11-slim

WORKDIR /app

# 安装后端依赖
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY outputs/ ./outputs/

# 启动
EXPOSE ${PORT:-8080}
CMD uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8080}
