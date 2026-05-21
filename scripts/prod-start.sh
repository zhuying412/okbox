#!/usr/bin/env bash
# ─── OKBox 生产环境启动脚本 ──────────────────────────────────────────
# 使用 Docker Compose 生产配置启动所有服务（HTTP 模式）
# 服务就绪检查通过容器内命令和 Nginx 入口，不依赖对外端口
# 用法：./scripts/prod-start.sh
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
echo "  ║   OKBox 生产环境部署                  ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

info "检查前置条件..."
command -v docker >/dev/null 2>&1 || error "Docker 未安装"
command -v docker compose >/dev/null 2>&1 || error "Docker Compose 未安装"
success "Docker 环境就绪"

info "检查环境配置..."
ENV_FILE="$PROJECT_ROOT/deploy/.env"
[ ! -f "$ENV_FILE" ] && error "deploy/.env 不存在。请先复制 deploy/.env.example 并配置。"

SECRET_KEY=$(grep -E "^SECRET_KEY=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'" || echo "")
POSTGRES_PASSWORD=$(grep -E "^POSTGRES_PASSWORD=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'" || echo "")
NGINX_PORT=$(grep -E "^NGINX_PORT=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'" || echo "80")
NGINX_PORT="${NGINX_PORT:-80}"

[ "${SECRET_KEY}" = "change-me-in-production" ] || [ -z "${SECRET_KEY}" ] && error "SECRET_KEY 必须修改！生成命令: openssl rand -hex 32"
[ "${POSTGRES_PASSWORD}" = "okbox" ] || [ -z "${POSTGRES_PASSWORD}" ] && warn "POSTGRES_PASSWORD 仍为默认值，建议修改"
success "环境配置验证通过"

info "构建生产 Docker 镜像..."
cd "$PROJECT_ROOT/deploy"
docker compose -f docker-compose.prod.yml build

info "启动生产环境服务..."
docker compose -f docker-compose.prod.yml up -d

info "执行健康检查..."

for i in $(seq 1 60); do
    if docker compose -f docker-compose.prod.yml exec -T postgres pg_isready -U okbox >/dev/null 2>&1; then
        success "PostgreSQL 已就绪"; break
    fi
    [ "$i" -eq 60 ] && error "PostgreSQL 启动超时"
    sleep 1
done

for i in $(seq 1 30); do
    if docker compose -f docker-compose.prod.yml exec -T redis redis-cli ping >/dev/null 2>&1; then
        success "Redis 已就绪"; break
    fi
    [ "$i" -eq 30 ] && warn "Redis 可能未就绪"
    sleep 1
done

for i in $(seq 1 90); do
    if docker compose -f docker-compose.prod.yml exec -T backend curl -sf http://localhost:8000/api/v1/health >/dev/null 2>&1; then
        success "后端 API 已就绪"; break
    fi
    [ "$i" -eq 90 ] && error "后端 API 启动超时。查看日志: docker compose -f docker-compose.prod.yml logs backend"
    sleep 2
done

for i in $(seq 1 30); do
    if curl -sf "http://localhost:${NGINX_PORT}/api/v1/health" >/dev/null 2>&1; then
        success "应用健康检查通过（Nginx 端口 ${NGINX_PORT}）"; break
    fi
    [ "$i" -eq 30 ] && error "Nginx 健康检查超时。查看日志: docker compose -f docker-compose.prod.yml logs nginx"
    sleep 2
done

RUNNING=$(docker compose -f docker-compose.prod.yml ps --format "{{.Service}}: {{.Status}}" | grep -c "running" || true)
TOTAL=$(docker compose -f docker-compose.prod.yml ps --format "{{.Service}}" | wc -l)
[ "$RUNNING" -eq "$TOTAL" ] && success "全部 $TOTAL 个服务正在运行" || { warn "仅 $RUNNING/$TOTAL 个服务在运行"; docker compose -f docker-compose.prod.yml ps; }

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  生产环境启动成功！${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BLUE}应用地址:${NC}     http://localhost:${NGINX_PORT}"
echo -e "  ${BLUE}API 健康检查:${NC} http://localhost:${NGINX_PORT}/api/v1/health"
echo ""
echo -e "  ${YELLOW}注意: 仅 Nginx 端口(${NGINX_PORT})对外暴露，其他服务在内部网络通信${NC}"
echo ""
echo -e "  ${YELLOW}常用命令:${NC}"
echo -e "    查看日志: docker compose -f deploy/docker-compose.prod.yml logs -f"
echo -e "    查看状态: ./scripts/status.sh"
echo -e "    停止服务: ./scripts/stop.sh"
echo -e "    重启服务: ./scripts/restart.sh"
echo ""
