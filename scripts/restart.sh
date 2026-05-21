#!/usr/bin/env bash
# ─── OKBox 重启脚本 ─────────────────────────────────────────────────
# 用法：./scripts/restart.sh [service_name]
# 不指定服务名则重启全部服务
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[信息]${NC} $1"; }
success() { echo -e "${GREEN}[完成]${NC} $1"; }

SERVICE="${1:-}"

cd "$PROJECT_ROOT/deploy"

# 检测当前运行的是哪个配置
if docker compose -f docker-compose.prod.yml ps --quiet 2>/dev/null | grep -q .; then
    COMPOSE_FILE="docker-compose.prod.yml"
    ENV_NAME="生产"
else
    COMPOSE_FILE="docker-compose.yml"
    ENV_NAME="开发"
fi

if [ -n "$SERVICE" ]; then
    info "重启${ENV_NAME}环境服务: $SERVICE"
    docker compose -f "$COMPOSE_FILE" restart "$SERVICE"
    success "服务 '$SERVICE' 已重启"
else
    info "重启${ENV_NAME}环境所有服务..."
    docker compose -f "$COMPOSE_FILE" restart
    success "所有服务已重启"
fi

# 显示当前状态
echo ""
info "当前服务状态:"
docker compose -f "$COMPOSE_FILE" ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}"
