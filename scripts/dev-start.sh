#!/usr/bin/env bash
# ─── OKBox 开发环境启动脚本 ──────────────────────────────────────────
# 使用 Docker Compose 启动所有服务（包括后端和前端的热重载模式）
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

# ─── 使用 Docker Compose 启动所有服务 ────────────────────────────
info "使用 Docker Compose 启动所有开发服务..."

cd "$PROJECT_ROOT/deploy"
docker compose up -d --build

# ─── 等待服务就绪 ────────────────────────────────────────────────
info "等待服务就绪..."

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

# 等待后端就绪
for i in $(seq 1 60); do
    if curl -sf http://localhost:8000/api/v1/health >/dev/null 2>&1; then
        success "后端 API 已就绪"
        break
    fi
    if [ "$i" -eq 60 ]; then
        warn "后端 API 启动较慢，请检查日志：docker compose logs backend"
    fi
    sleep 2
done

# ─── 输出访问信息 ────────────────────────────────────────────────
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  开发环境启动成功！${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BLUE}前端（Vite HMR）:${NC}  http://localhost:3000"
echo -e "  ${BLUE}后端 API:${NC}         http://localhost:8000"
echo -e "  ${BLUE}API 文档:${NC}         http://localhost:8000/api/docs"
echo -e "  ${BLUE}Nginx 代理:${NC}       http://localhost"
echo -e "  ${BLUE}MinIO 控制台:${NC}     http://localhost:9001 (minioadmin/minioadmin)"
echo ""
echo -e "  ${YELLOW}常用命令:${NC}"
echo -e "    查看日志:     docker compose -f deploy/docker-compose.yml logs -f"
echo -e "    查看后端日志: docker compose -f deploy/docker-compose.yml logs -f backend"
echo -e "    查看前端日志: docker compose -f deploy/docker-compose.yml logs -f frontend"
echo -e "    停止服务:     ./scripts/stop.sh"
echo -e "    重启服务:     ./scripts/restart.sh"
echo ""
echo -e "  ${YELLOW}热重载说明:${NC}"
echo -e "    后端: 修改 packages/backend/src/ 下代码后自动重载"
echo -e "    前端: 修改 packages/frontend/src/ 下代码后自动热更新"
echo ""
