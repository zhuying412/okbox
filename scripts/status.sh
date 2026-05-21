#!/usr/bin/env bash
# ─── OKBox 状态检查脚本 ─────────────────────────────────────────────
# 用法：./scripts/status.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

info() { echo -e "${BLUE}[信息]${NC} $1"; }
success() { echo -e "${GREEN}[完成]${NC} $1"; }
warn() { echo -e "${YELLOW}[警告]${NC} $1"; }

echo -e "${CYAN}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║   OKBox 服务状态                      ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

cd "$PROJECT_ROOT/deploy"

# ─── Docker 服务状态 ─────────────────────────────────────────────
info "Docker Compose 服务:"
echo ""

# 检测当前运行的配置
if docker compose -f docker-compose.prod.yml ps --quiet 2>/dev/null | grep -q .; then
    COMPOSE_FILE="docker-compose.prod.yml"
    echo -e "  环境: ${GREEN}生产${NC}"
else
    COMPOSE_FILE="docker-compose.yml"
    echo -e "  环境: ${CYAN}开发${NC}"
fi
echo ""

docker compose -f "$COMPOSE_FILE" ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || \
    warn "未发现运行中的 Docker Compose 服务"

# ─── 健康检查 ────────────────────────────────────────────────────
echo ""
info "健康检查:"

if curl -sf http://localhost:8000/api/v1/health >/dev/null 2>&1; then
    success "后端 API:    http://localhost:8000 (健康)"
elif curl -sf http://localhost/api/v1/health >/dev/null 2>&1; then
    success "后端 API:    http://localhost (通过 Nginx，健康)"
else
    warn "后端 API:    未响应"
fi

if docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U okbox >/dev/null 2>&1; then
    success "PostgreSQL:  端口 5432 (就绪)"
else
    warn "PostgreSQL:  未就绪"
fi

if docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping >/dev/null 2>&1; then
    success "Redis:       端口 6379 (就绪)"
else
    warn "Redis:       未就绪"
fi

if curl -sf http://localhost:9000/minio/health/ready >/dev/null 2>&1; then
    success "MinIO:       端口 9000 (就绪)"
else
    warn "MinIO:       未就绪"
fi

# ─── 端口使用情况 ────────────────────────────────────────────────
echo ""
info "端口使用:"

for port in 80 3000 5432 6379 8000 9000 9001; do
    if lsof -i :"${port}" >/dev/null 2>&1; then
        echo -e "  端口 ${GREEN}${port}${NC}: 使用中"
    else
        echo -e "  端口 ${YELLOW}${port}${NC}: 空闲"
    fi
done

# ─── 资源使用 ────────────────────────────────────────────────────
echo ""
info "容器资源使用:"
echo ""
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>/dev/null | head -10 || \
    warn "无法获取容器资源信息"

echo ""
success "状态检查完成"
