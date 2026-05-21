#!/usr/bin/env bash
# ─── OKBox 开发环境启动脚本 ──────────────────────────────────────────
# 使用 Docker Compose 启动所有服务（包括后端和前端的热重载模式）
# 服务就绪检查通过 docker compose exec（容器内执行），不依赖对外端口
# 用法：./scripts/dev-start.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[信息]${NC} $1"; }
success() { echo -e "${GREEN}[完成]${NC} $1"; }
warn() { echo -e "${YELLOW}[警告]${NC} $1"; }
error() { echo -e "${RED}[错误]${NC} $1"; exit 1; }

echo -e "${GREEN}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║   OKBox 开发环境                      ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

# ─── 检查前置条件 ────────────────────────────────────────────────
info "检查前置条件..."

command -v docker >/dev/null 2>&1 || error "Docker 未安装"
command -v docker compose >/dev/null 2>&1 || error "Docker Compose 未安装"
success "Docker 环境就绪"

# ─── 初始化环境文件 ──────────────────────────────────────────────
info "检查环境配置..."

if [ ! -f "$PROJECT_ROOT/deploy/.env" ]; then
    if [ -f "$PROJECT_ROOT/deploy/.env.example" ]; then
        cp "$PROJECT_ROOT/deploy/.env.example" "$PROJECT_ROOT/deploy/.env"
        success "已从 .env.example 创建 deploy/.env"
    fi
fi

# ─── 读取 Nginx 端口配置 ─────────────────────────────────────────
NGINX_PORT=$(grep -E "^NGINX_PORT=" "$PROJECT_ROOT/deploy/.env" 2>/dev/null | cut -d'=' -f2- | tr -d '"' | tr -d "'" || echo "80")
NGINX_PORT="${NGINX_PORT:-80}"

# ─── 使用 Docker Compose 启动所有服务 ────────────────────────────
info "使用 Docker Compose 启动所有开发服务..."

cd "$PROJECT_ROOT/deploy"
docker compose up -d --build

# ─── 等待服务就绪（通过容器内命令检查，不依赖对外端口）─────────
info "等待服务就绪..."

# PostgreSQL（容器内检查）
for i in $(seq 1 60); do
    if docker compose exec -T postgres pg_isready -U okbox >/dev/null 2>&1; then
        success "PostgreSQL 已就绪"
        break
    fi
    if [ "$i" -eq 60 ]; then
        error "PostgreSQL 启动超时（60秒）"
    fi
    sleep 1
done

# Redis（容器内检查）
for i in $(seq 1 30); do
    if docker compose exec -T redis redis-cli ping >/dev/null 2>&1; then
        success "Redis 已就绪"
        break
    fi
    if [ "$i" -eq 30 ]; then
        warn "Redis 可能未就绪"
    fi
    sleep 1
done

# 后端 API（容器内检查）
for i in $(seq 1 90); do
    if docker compose exec -T backend curl -sf http://localhost:8000/api/v1/health >/dev/null 2>&1; then
        success "后端 API 已就绪"
        break
    fi
    if [ "$i" -eq 90 ]; then
        warn "后端 API 启动较慢，请检查日志：docker compose logs backend"
    fi
    sleep 2
done

# 通过 Nginx 入口验证整体服务可用性
for i in $(seq 1 60); do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${NGINX_PORT}/api/v1/health 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        success "Nginx 代理已就绪（整体服务可用）"
        break
    fi
    if [ "$i" -eq 60 ]; then
        warn "Nginx 可能未就绪，HTTP 状态码: ${HTTP_CODE}"
        warn "响应内容："
        curl -s http://localhost:${NGINX_PORT}/api/v1/health 2>&1 | head -5 || true
        warn "请检查日志：docker compose logs nginx backend"
    fi
    sleep 2
done

# ─── 输出访问信息 ────────────────────────────────────────────────
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  开发环境启动成功！${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
if [ "$NGINX_PORT" = "80" ]; then
    echo -e "  ${BLUE}应用入口:${NC}     http://localhost"
    echo -e "  ${BLUE}API 文档:${NC}     http://localhost/api/docs"
else
    echo -e "  ${BLUE}应用入口:${NC}     http://localhost:${NGINX_PORT}"
    echo -e "  ${BLUE}API 文档:${NC}     http://localhost:${NGINX_PORT}/api/docs"
fi
echo ""
echo -e "  ${YELLOW}注意: 所有服务通过 Nginx 代理访问，仅对外暴露端口 ${NGINX_PORT}${NC}"
echo ""
echo -e "  ${YELLOW}常用命令:${NC}"
echo -e "    查看日志:     docker compose -f deploy/docker-compose.yml logs -f"
echo -e "    查看后端日志: docker compose -f deploy/docker-compose.yml logs -f backend"
echo -e "    查看前端日志: docker compose -f deploy/docker-compose.yml logs -f frontend"
echo -e "    停止服务:     ./scripts/stop.sh"
echo -e "    重启服务:     ./scripts/restart.sh"
echo -e "    查看状态:     ./scripts/status.sh"
echo ""
echo -e "  ${YELLOW}热重载说明:${NC}"
echo -e "    后端: 修改 packages/backend/src/ 下代码后自动重载"
echo -e "    前端: 修改 packages/frontend/src/ 下代码后自动热更新"
echo ""
echo -e "  ${YELLOW}调试提示（需要直接访问内部服务时）:${NC}"
echo -e "    PostgreSQL: docker compose exec postgres psql -U okbox"
echo -e "    Redis CLI:  docker compose exec redis redis-cli"
echo ""
