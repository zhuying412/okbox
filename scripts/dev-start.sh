#!/usr/bin/env bash
# ─── OKBox 开发环境启动脚本 ──────────────────────────────────────────
# 使用 Docker Compose 启动所有服务（包括后端和前端的热重载模式）
# 服务就绪检查通过 docker compose exec（容器内执行），不依赖对外端口
# 用法：./scripts/dev-start.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info() { echo -e "${BLUE}[信息]${NC} $1"; }
success() { echo -e "${GREEN}[完成]${NC} $1"; }
warn() { echo -e "${YELLOW}[警告]${NC} $1"; }
error() { echo -e "${RED}[错误]${NC} $1"; exit 1; }

echo -e "${GREEN}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║   OKBox 开发环境                      ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

info "检查前置条件..."
command -v docker >/dev/null 2>&1 || error "Docker 未安装"
command -v docker compose >/dev/null 2>&1 || error "Docker Compose 未安装"
success "Docker 环境就绪"

info "检查环境配置..."
if [ ! -f "$PROJECT_ROOT/deploy/.env" ]; then
    if [ -f "$PROJECT_ROOT/deploy/.env.example" ]; then
        cp "$PROJECT_ROOT/deploy/.env.example" "$PROJECT_ROOT/deploy/.env"
        success "已从 .env.example 创建 deploy/.env"
    fi
fi

# 读取 Nginx 端口配置
NGINX_PORT=$(grep -E "^NGINX_PORT=" "$PROJECT_ROOT/deploy/.env" 2>/dev/null | cut -d'=' -f2- | tr -d '"' | tr -d "'" || echo "80")
NGINX_PORT="${NGINX_PORT:-80}"

info "使用 Docker Compose 启动所有开发服务..."
cd "$PROJECT_ROOT/deploy"
docker compose up -d --build

info "等待服务就绪..."

for i in $(seq 1 60); do
    if docker compose exec -T postgres pg_isready -U okbox >/dev/null 2>&1; then
        success "PostgreSQL 已就绪"; break
    fi
    [ "$i" -eq 60 ] && error "PostgreSQL 启动超时（60秒）"
    sleep 1
done

for i in $(seq 1 30); do
    if docker compose exec -T redis redis-cli ping >/dev/null 2>&1; then
        success "Redis 已就绪"; break
    fi
    [ "$i" -eq 30 ] && warn "Redis 可能未就绪"
    sleep 1
done

for i in $(seq 1 90); do
    if docker compose exec -T backend curl -sf http://localhost:8000/api/v1/health >/dev/null 2>&1; then
        success "后端 API 已就绪"; break
    fi
    [ "$i" -eq 90 ] && warn "后端 API 启动较慢，请检查日志：docker compose logs backend"
    sleep 2
done

for i in $(seq 1 30); do
    if curl -sf "http://localhost:${NGINX_PORT}/api/v1/health" >/dev/null 2>&1; then
        success "Nginx 代理已就绪（端口 ${NGINX_PORT}）"; break
    fi
    [ "$i" -eq 30 ] && warn "Nginx 可能未就绪，请检查日志：docker compose logs nginx"
    sleep 2
done

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  开发环境启动成功！${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BLUE}应用入口:${NC}     http://localhost:${NGINX_PORT}"
echo -e "  ${BLUE}API 文档:${NC}     http://localhost:${NGINX_PORT}/api/docs"
echo ""
echo -e "  ${YELLOW}注意: 所有服务通过 Nginx 代理访问，不对外暴露其他端口${NC}"
echo ""
echo -e "  ${YELLOW}常用命令:${NC}"
echo -e "    查看日志:     docker compose -f deploy/docker-compose.yml logs -f"
echo -e "    停止服务:     ./scripts/stop.sh"
echo -e "    重启服务:     ./scripts/restart.sh"
echo -e "    查看状态:     ./scripts/status.sh"
echo ""
echo -e "  ${YELLOW}调试提示:${NC}"
echo -e "    PostgreSQL: docker compose -f deploy/docker-compose.yml exec postgres psql -U okbox"
echo -e "    Redis CLI:  docker compose -f deploy/docker-compose.yml exec redis redis-cli"
echo ""
