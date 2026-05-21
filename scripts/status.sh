#!/usr/bin/env bash
# ─── OKBox 状态检查脚本 ─────────────────────────────────────────────
# 通过 docker compose exec 在容器内执行检查，不依赖对外暴露端口
# Nginx 端口从 .env 配置读取
# 用法：./scripts/status.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'
info() { echo -e "${BLUE}[信息]${NC} $1"; }
success() { echo -e "${GREEN}[完成]${NC} $1"; }
warn() { echo -e "${YELLOW}[警告]${NC} $1"; }

echo -e "${CYAN}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║   OKBox 服务状态                      ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

cd "$PROJECT_ROOT/deploy"

# 读取 Nginx 端口配置
NGINX_PORT=$(grep -E "^NGINX_PORT=" .env 2>/dev/null | cut -d'=' -f2- | tr -d '"' | tr -d "'" || echo "80")
NGINX_PORT="${NGINX_PORT:-80}"

# 检测当前环境
if docker compose -f docker-compose.prod.yml ps --quiet 2>/dev/null | grep -q .; then
    COMPOSE_FILE="docker-compose.prod.yml"
    echo -e "  环境: ${GREEN}生产${NC}"
else
    COMPOSE_FILE="docker-compose.yml"
    echo -e "  环境: ${CYAN}开发${NC}"
fi
echo ""

info "Docker Compose 服务:"
echo ""
docker compose -f "$COMPOSE_FILE" ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || \
    warn "未发现运行中的 Docker Compose 服务"

echo ""
info "健康检查（容器内执行）:"

if curl -sf "http://localhost:${NGINX_PORT}/api/v1/health" >/dev/null 2>&1; then
    success "应用入口:    http://localhost:${NGINX_PORT} (健康)"
else
    warn "应用入口:    http://localhost:${NGINX_PORT} (未响应)"
fi

if docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U okbox >/dev/null 2>&1; then
    success "PostgreSQL:  就绪"
else
    warn "PostgreSQL:  未就绪"
fi

if docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping >/dev/null 2>&1; then
    success "Redis:       就绪"
else
    warn "Redis:       未就绪"
fi

if docker compose -f "$COMPOSE_FILE" exec -T backend curl -sf http://localhost:8000/api/v1/health >/dev/null 2>&1; then
    success "后端 API:    就绪"
else
    warn "后端 API:    未就绪"
fi

if docker compose -f "$COMPOSE_FILE" exec -T minio curl -sf http://localhost:9000/minio/health/ready >/dev/null 2>&1; then
    success "MinIO:       就绪"
else
    warn "MinIO:       未就绪"
fi

echo ""
info "对外端口（仅 Nginx 端口 ${NGINX_PORT}）:"
if lsof -i :"${NGINX_PORT}" >/dev/null 2>&1; then
    echo -e "  端口 ${GREEN}${NGINX_PORT}${NC}: Nginx 运行中"
else
    echo -e "  端口 ${YELLOW}${NGINX_PORT}${NC}: 空闲"
fi

echo ""
info "容器资源使用:"
echo ""
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>/dev/null | head -10 || \
    warn "无法获取容器资源信息"

echo ""
success "状态检查完成"
