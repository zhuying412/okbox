#!/usr/bin/env bash
# ─── OKBox Stop Script ───────────────────────────────────────────────
# Usage: ./scripts/stop.sh [--remove-volumes]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

REMOVE_VOLUMES=false

for arg in "$@"; do
    case $arg in
        --remove-volumes)
            REMOVE_VOLUMES=true
            ;;
        -h|--help)
            echo "Usage: $0 [--remove-volumes]"
            echo ""
            echo "Options:"
            echo "  --remove-volumes  Remove data volumes (WARNING: destroys all data)"
            echo "  -h, --help        Show this help"
            exit 0
            ;;
    esac
done

info "Stopping OKBox services..."

cd "$PROJECT_ROOT/deploy"

if [ "$REMOVE_VOLUMES" = true ]; then
    warn "Removing containers AND data volumes..."
    echo -n "  Are you sure? This will DELETE all data (y/N): "
    read -r confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        docker compose down -v
        success "All services stopped and volumes removed"
    else
        info "Aborted. Stopping without removing volumes..."
        docker compose down
        success "All services stopped (volumes preserved)"
    fi
else
    docker compose down
    success "All services stopped (volumes preserved)"
fi

# Kill any remaining dev processes
if pgrep -f "uvicorn okbox.main:app" >/dev/null 2>&1; then
    info "Stopping backend dev server..."
    pkill -f "uvicorn okbox.main:app" || true
fi

if pgrep -f "vite" >/dev/null 2>&1; then
    info "Stopping frontend dev server..."
    pkill -f "vite.*packages/frontend" || true
fi

success "Done."
