#!/usr/bin/env bash
# ─── OKBox Status Check Script ───────────────────────────────────────
# Usage: ./scripts/status.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

echo -e "${CYAN}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║   OKBox Service Status                ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

# ─── Docker Services Status ──────────────────────────────────────────
info "Docker Compose services:"
echo ""

cd "$PROJECT_ROOT/deploy"

if docker compose ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null; then
    echo ""
else
    warn "No Docker Compose services found or Docker is not running"
fi

# ─── Health Checks ───────────────────────────────────────────────────
echo ""
info "Health checks:"

# Backend API
if curl -sf http://localhost:8000/api/v1/health >/dev/null 2>&1; then
    success "Backend API:   http://localhost:8000 (healthy)"
elif curl -sf https://localhost/api/v1/health -k >/dev/null 2>&1; then
    success "Backend API:   https://localhost (healthy via Nginx)"
else
    warn "Backend API:   NOT RESPONDING"
fi

# PostgreSQL
if docker compose exec -T postgres pg_isready -U okbox >/dev/null 2>&1; then
    success "PostgreSQL:    port 5432 (ready)"
else
    warn "PostgreSQL:    NOT READY"
fi

# Redis
if docker compose exec -T redis redis-cli ping >/dev/null 2>&1; then
    success "Redis:         port 6379 (ready)"
else
    warn "Redis:         NOT READY"
fi

# MinIO
if curl -sf http://localhost:9000/minio/health/ready >/dev/null 2>&1; then
    success "MinIO:         port 9000 (ready)"
else
    warn "MinIO:         NOT READY"
fi

# ─── Port Usage ──────────────────────────────────────────────────────
echo ""
info "Port usage:"

for port in 80 443 3000 5432 6379 8000 9000 9001; do
    if lsof -i :"${port}" >/dev/null 2>&1; then
        echo -e "  Port ${GREEN}${port}${NC}: in use"
    else
        echo -e "  Port ${YELLOW}${port}${NC}: free"
    fi
done

# ─── Resource Usage ──────────────────────────────────────────────────
echo ""
info "Resource usage (Docker containers):"
echo ""

docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>/dev/null | head -10 || warn "Unable to get container stats"

# ─── Disk Usage ──────────────────────────────────────────────────────
echo ""
info "Docker disk usage:"
docker system df 2>/dev/null || warn "Unable to get Docker disk usage"

echo ""
success "Status check complete"
