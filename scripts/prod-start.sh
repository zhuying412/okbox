#!/usr/bin/env bash
# ─── OKBox 生产环境启动脚本 ──────────────────────────────────────────
# 使用 Docker Compose 生产配置启动所有服务（HTTP 模式）
# 服务就绪检查通过 Nginx 入口和 docker compose exec，不依赖对外端口
# 用法：./scripts/prod-start.sh
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
echo "  ║   OKBox 生产环境部署                  ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

# ─── 检查前置条件 ────────────────────────────────────────────────
info "检查前置条件..."

command -v docker >/dev/null 2>&1 || error "Docker 未安装"
command -v docker compose >/dev/null 2>&1 || error "Docker Compose 未安装"
success "Docker 环境就绪"

# ─── 检查环境配置 ────────────────────────────────────────────────
info "检查环境配置..."

ENV_FILE="$PROJECT_ROOT/deploy/.env"

if [ ! -f "$ENV_FILE" ]; then
    error "deploy/.env 不存在。请先复制 deploy/.env.example 并配置。"
fi

# 安全读取环境变量（不使用 source）
SECRET_KEY=$(grep -E "^SECRET_KEY=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'" || echo "")
POSTGRES_PASSWORD=$(grep -E "^POSTGRES_PASSWORD=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'" || echo "")

if [ "${SECRET_KEY}" = "change-me-in-production" ] || [ -z "${SECRET_KEY}" ]; then
    error "SECRET_KEY 必须修改！生成命令: openssl rand -hex 32"
fi

if [ "${POSTGRES_PASSWORD}" = "okbox" ] || [ -z "${POSTGRES_PASSWORD}" ]; then
    warn "POSTGRES_PASSWORD 仍为默认值，建议修改"
fi

success "环境配置验证通过"

# ─── 读取 Nginx 端口配置 ─────────────────────────────────────────
NGINX_PORT=$(grep -E "^NGINX_PORT=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'" || echo "80")
NGINX_PORT="${NGINX_PORT:-80}"

# ─── 构建生产镜像 ────────────────────────────────────────────────
info "构建生产 Docker 镜像..."

cd "$PROJECT_ROOT/deploy"
docker compose -f docker-compose.prod.yml build

# ─── 启动生产服务 ────────────────────────────────────────────────
info "启动生产环境服务..."

docker compose -f docker-compose.prod.yml up -d

# ─── 健康检查（通过容器内命令和 Nginx 入口）──────────────────────
info "执行健康检查..."

# 基础服务检查（容器内执行）
for i in $(seq 1 60); do
    if docker compose -f docker-compose.prod.yml exec -T postgres pg_isready -U okbox >/dev/null 2>&1; then
        success "PostgreSQL 已就绪"
        break
    fi
    if [ "$i" -eq 60 ]; then
        error "PostgreSQL 启动超时"
    fi
    sleep 1
done

for i in $(seq 1 30); do
    if docker compose -f docker-compose.prod.yml exec -T redis redis-cli ping >/dev/null 2>&1; then
        success "Redis 已就绪"
        break
    fi
    if [ "$i" -eq 30 ]; then
        warn "Redis 可能未就绪"
    fi
    sleep 1
done

# 通过 Nginx 入口检查整体可用性
for i in $(seq 1 60); do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${NGINX_PORT}/api/v1/health 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        success "应用健康检查通过（通过 Nginx 入口）"
        break
    fi
    if [ "$i" -eq 60 ]; then
        error "应用健康检查超时（60秒），HTTP 状态码: ${HTTP_CODE}
响应: $(curl -s http://localhost:${NGINX_PORT}/api/v1/health 2>&1 | head -3)
查看日志: docker compose -f docker-compose.prod.yml logs backend"
    fi
    sleep 2
done

# 检查所有容器状态
RUNNING=$(docker compose -f docker-compose.prod.yml ps --format "{{.Service}}: {{.Status}}" | grep -c "running" || true)
TOTAL=$(docker compose -f docker-compose.prod.yml ps --format "{{.Service}}" | wc -l)

if [ "$RUNNING" -eq "$TOTAL" ]; then
    success "全部 $TOTAL 个服务正在运行"
else
    warn "仅 $RUNNING/$TOTAL 个服务在运行"
    docker compose -f docker-compose.prod.yml ps
fi

# ─── 输出状态 ────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  生产环境启动成功！${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
if [ "$NGINX_PORT" = "80" ]; then
    echo -e "  ${BLUE}应用地址:${NC}     http://localhost"
    echo -e "  ${BLUE}API 健康检查:${NC} http://localhost/api/v1/health"
else
    echo -e "  ${BLUE}应用地址:${NC}     http://localhost:${NGINX_PORT}"
    echo -e "  ${BLUE}API 健康检查:${NC} http://localhost:${NGINX_PORT}/api/v1/health"
fi
echo ""
echo -e "  ${YELLOW}注意: 仅 Nginx 端口(${NGINX_PORT})对外暴露，其他服务在内部网络通信${NC}"
echo ""
echo -e "  ${YELLOW}常用命令:${NC}"
echo -e "    查看日志: docker compose -f deploy/docker-compose.prod.yml logs -f"
echo -e "    查看状态: ./scripts/status.sh"
echo -e "    停止服务: ./scripts/stop.sh"
echo -e "    重启服务: ./scripts/restart.sh"
echo ""
