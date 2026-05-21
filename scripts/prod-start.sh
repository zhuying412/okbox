#!/usr/bin/env bash
# ─── OKBox Production Environment Startup Script ─────────────────────
# Usage: ./scripts/prod-start.sh
# Prerequisites: Docker, Docker Compose
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
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo -e "${GREEN}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║   OKBox Production Deployment         ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

# ─── Check Prerequisites ────────────────────────────────────────────
info "Checking prerequisites..."

command -v docker >/dev/null 2>&1 || error "Docker is not installed"
command -v docker compose >/dev/null 2>&1 || error "Docker Compose is not installed"

# ─── Check Environment Configuration ────────────────────────────────
info "Checking environment configuration..."

ENV_FILE="$PROJECT_ROOT/deploy/.env"

if [ ! -f "$ENV_FILE" ]; then
    error "deploy/.env not found. Copy deploy/.env.example and configure it first."
fi

# Check critical environment variables (safely read without sourcing)
SECRET_KEY=$(grep -E "^SECRET_KEY=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'" || echo "")
POSTGRES_PASSWORD=$(grep -E "^POSTGRES_PASSWORD=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'" || echo "")
MINIO_SECRET_KEY=$(grep -E "^MINIO_SECRET_KEY=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'" || echo "")

if [ "${SECRET_KEY}" = "change-me-in-production" ] || [ -z "${SECRET_KEY}" ]; then
    error "SECRET_KEY must be changed from default value! Generate with: openssl rand -hex 32"
fi

if [ "${POSTGRES_PASSWORD}" = "okbox" ]; then
    warn "POSTGRES_PASSWORD is still the default value. Consider changing for production."
fi

if [ "${MINIO_SECRET_KEY}" = "minioadmin" ]; then
    warn "MINIO_SECRET_KEY is still the default value. Consider changing for production."
fi

success "Environment configuration validated"

# ─── Check SSL Certificate ───────────────────────────────────────────
info "Checking SSL certificate..."

if [ ! -f "$PROJECT_ROOT/deploy/nginx/ssl/okbox.crt" ]; then
    warn "SSL certificate not found. Generating self-signed certificate..."
    bash "$PROJECT_ROOT/deploy/nginx/generate-cert.sh"
    success "Self-signed certificate generated"
else
    success "SSL certificate found"
fi

# ─── Build and Start Services ────────────────────────────────────────
info "Building Docker images..."

cd "$PROJECT_ROOT/deploy"
docker compose build --no-cache

info "Starting production services..."
docker compose up -d

# ─── Health Check ────────────────────────────────────────────────────
info "Running health checks..."

# Wait for backend to be ready
for i in $(seq 1 60); do
    if curl -sf https://localhost/api/v1/health -k >/dev/null 2>&1; then
        success "Backend API is healthy (via Nginx HTTPS)"
        break
    fi
    if [ "$i" -eq 60 ]; then
        error "Backend failed health check within 60 seconds. Check logs: docker compose logs backend"
    fi
    sleep 2
done

# Check all containers are running
RUNNING=$(docker compose ps --format "{{.Service}}: {{.Status}}" | grep -c "running" || true)
TOTAL=$(docker compose ps --format "{{.Service}}" | wc -l)

if [ "$RUNNING" -eq "$TOTAL" ]; then
    success "All $TOTAL services are running"
else
    warn "Only $RUNNING/$TOTAL services are running"
    docker compose ps
fi

# ─── Print Status ────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Production environment started successfully!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BLUE}Application:${NC}  https://localhost"
echo -e "  ${BLUE}API Health:${NC}   https://localhost/api/v1/health"
echo ""
echo -e "  ${YELLOW}Useful commands:${NC}"
echo -e "    View logs:     docker compose -f deploy/docker-compose.yml logs -f"
echo -e "    View status:   ./scripts/status.sh"
echo -e "    Stop services: ./scripts/stop.sh"
echo -e "    Restart:       ./scripts/restart.sh"
echo ""
