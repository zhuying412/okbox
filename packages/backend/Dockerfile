FROM python:3.12-slim AS base

WORKDIR /app

# 配置国内 apt 源（阿里云）加速系统包安装
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list 2>/dev/null || true

# 安装 curl（健康检查依赖）
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 配置 uv/pip 国内源（清华源）
ENV UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# Copy dependency files
COPY pyproject.toml .

# Install dependencies only (利用 Docker 层缓存)
RUN uv sync --no-dev --no-install-project

# Copy source code
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .

# Install project itself (使 okbox 模块可被 Python 导入)
RUN uv sync --no-dev

# Expose port
EXPOSE 8000

# Run application
CMD ["uv", "run", "uvicorn", "okbox.main:app", "--host", "0.0.0.0", "--port", "8000"]
