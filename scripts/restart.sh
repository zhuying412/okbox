#!/usr/bin/env bash
# ─── OKBox Restart Script ────────────────────────────────────────────
# Usage: ./scripts/restart.sh [service_name]
# If no service specified, restarts all services.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }

SERVICE="${1:-}"

cd "$PROJECT_ROOT/deploy"

if [ -n "$SERVICE" ]; then
    info "Restarting service: $SERVICE"
    docker compose restart "$SERVICE"
    success "Service '$SERVICE' restarted"
else
    info "Restarting all OKBox services..."
    docker compose restart
    success "All services restarted"
fi

# Show status after restart
echo ""
info "Current service status:"
docker compose ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}"
