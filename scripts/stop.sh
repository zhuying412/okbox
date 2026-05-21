#!/usr/bin/env bash
# ─── OKBox 停止脚本 ─────────────────────────────────────────────────
# 用法：./scripts/stop.sh [--remove-volumes]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[信息]${NC} $1"; }
success() { echo -e "${GREEN}[完成]${NC} $1"; }
warn() { echo -e "${YELLOW}[警告]${NC} $1"; }

REMOVE_VOLUMES=false

for arg in "$@"; do
    case $arg in
        --remove-volumes)
            REMOVE_VOLUMES=true
            ;;
        -h|--help)
            echo "用法: $0 [--remove-volumes]"
            echo ""
            echo "选项:"
            echo "  --remove-volumes  删除数据卷（警告：将销毁所有数据）"
            echo "  -h, --help        显示帮助"
            exit 0
            ;;
    esac
done

info "停止 OKBox 服务..."

cd "$PROJECT_ROOT/deploy"

# 尝试停止开发环境
if docker compose ps --quiet 2>/dev/null | grep -q .; then
    if [ "$REMOVE_VOLUMES" = true ]; then
        warn "将删除容器和数据卷..."
        echo -n "  确定吗？这将删除所有数据 (y/N): "
        read -r confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            docker compose down -v
            success "所有服务已停止，数据卷已删除"
        else
            docker compose down
            success "所有服务已停止（数据卷保留）"
        fi
    else
        docker compose down
        success "开发环境服务已停止（数据卷保留）"
    fi
fi

# 尝试停止生产环境
if docker compose -f docker-compose.prod.yml ps --quiet 2>/dev/null | grep -q .; then
    if [ "$REMOVE_VOLUMES" = true ]; then
        docker compose -f docker-compose.prod.yml down -v
        success "生产环境服务已停止，数据卷已删除"
    else
        docker compose -f docker-compose.prod.yml down
        success "生产环境服务已停止（数据卷保留）"
    fi
fi

success "完成"
