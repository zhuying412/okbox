#!/usr/bin/env bash
# ─── OKBox Development Environment Startup Script ───────────────────
# Usage: ./scripts/dev-start.sh
# Prerequisites: Docker, Docker Compose, Node.js (pnpm), Python (uv)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo -e "${GREEN}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║   OKBox Development Environment      ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

# ─── Check Prerequisites ────────────────────────────────────────────
info "Checking prerequisites..."

command -v docker >/dev/null 2>&1 || error "Docker is not installed"
command -v docker compose >/dev/null 2>&1 || error "Docker Compose is not installed"

if command -v uv >/dev/null 2>&1; then
    success "uv found: $(uv --version)"
elif command -v pip >/dev/null 2>&1; then
    warn "uv not found, will use pip"
else
    error "Neither uv nor pip is installed"
fi

if command -v pnpm >/dev/null 2>&1; then
    success "pnpm found: $(pnpm --version)"
elif command -v npm >/dev/null 2>&1; then
    warn "pnpm not found, will use npm"
else
    error "Neither pnpm nor npm is installed"
fi

# ─── Setup Environment File ─────────────────────────────────────────
info "Checking environment configuration..."

if [ ! -f "$PROJECT_ROOT/.env" ]; then
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        success "Created .env from .env.example"
    fi
fi

if [ ! -f "$PROJECT_ROOT/deploy/.env" ]; then
    if [ -f "$PROJECT_ROOT/deploy/.env.example" ]; then
        cp "$PROJECT_ROOT/deploy/.env.example" "$PROJECT_ROOT/deploy/.env"
        success "Created deploy/.env from deploy/.env.example"
    fi
fi

# ─── Start Docker Services (DB, Redis, MinIO) ───────────────────────
info "Starting Docker Compose development services..."

cd "$PROJECT_ROOT/deploy"
docker compose up -d postgres redis minio

# Wait for services to be healthy
info "Waiting for services to be ready..."
for i in $(seq 1 30); do
    if docker compose exec -T postgres pg_isready -U okbox >/dev/null 2>&1; then
        success "PostgreSQL is ready"
        break
    fi
    if [ "$i" -eq 30 ]; then
        error "PostgreSQL failed to start within 30 seconds"
    fi
    sleep 1
done

for i in $(seq 1 15); do
    if docker compose exec -T redis redis-cli ping >/dev/null 2>&1; then
        success "Redis is ready"
        break
    fi
    if [ "$i" -eq 15 ]; then
        warn "Redis may not be ready"
    fi
    sleep 1
done

success "Docker services started"

# ─── Install Backend Dependencies ────────────────────────────────────
info "Installing backend dependencies..."

cd "$PROJECT_ROOT/packages/backend"
if command -v uv >/dev/null 2>&1; then
    uv sync
else
    pip install -e ".[dev]"
fi
success "Backend dependencies installed"

# ─── Initialize Database ─────────────────────────────────────────────
info "Running database migrations..."

if command -v uv >/dev/null 2>&1; then
    uv run alembic upgrade head 2>/dev/null || warn "No migrations to run (alembic not configured yet)"
else
    alembic upgrade head 2>/dev/null || warn "No migrations to run (alembic not configured yet)"
fi
success "Database initialized"

# ─── Install Frontend Dependencies ───────────────────────────────────
info "Installing frontend dependencies..."

cd "$PROJECT_ROOT/packages/frontend"
if command -v pnpm >/dev/null 2>&1; then
    pnpm install
else
    npm install
fi
success "Frontend dependencies installed"

# ─── Start Development Servers ───────────────────────────────────────
info "Starting development servers..."

# Start backend (in background)
cd "$PROJECT_ROOT/packages/backend"
if command -v uv >/dev/null 2>&1; then
    uv run uvicorn okbox.main:app --reload --host 0.0.0.0 --port 8000 &
else
    python -m uvicorn okbox.main:app --reload --host 0.0.0.0 --port 8000 &
fi
BACKEND_PID=$!

# Start frontend (in background)
cd "$PROJECT_ROOT/packages/frontend"
if command -v pnpm >/dev/null 2>&1; then
    pnpm dev &
else
    npm run dev &
fi
FRONTEND_PID=$!

# ─── Print Access Information ────────────────────────────────────────
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Development environment started successfully!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BLUE}Frontend:${NC}   http://localhost:3000"
echo -e "  ${BLUE}Backend:${NC}    http://localhost:8000"
echo -e "  ${BLUE}API Docs:${NC}   http://localhost:8000/api/docs"
echo -e "  ${BLUE}MinIO:${NC}      http://localhost:9001 (admin/minioadmin)"
echo ""
echo -e "  ${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# ─── Handle Ctrl+C ──────────────────────────────────────────────────
cleanup() {
    echo ""
    info "Shutting down development servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    info "Stopping Docker services..."
    cd "$PROJECT_ROOT/deploy" && docker compose stop
    success "All services stopped"
}

trap cleanup EXIT INT TERM

# Wait for background processes
wait
