# Deployment Guide

## Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 8 cores | 16 cores |
| RAM | 32 GB | 64 GB |
| Storage | 500 GB SSD | 2 TB SSD (RAID) |
| Network | 1 Gbps | 10 Gbps |
| OS | CentOS 8+ / Ubuntu 22.04+ | Rocky Linux 9 |

## Software Dependencies

- Docker Engine 24+
- Docker Compose v2.20+
- Git 2.30+
- OpenSSL 3.0+

## Installation Steps

### 1. Prepare Host

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
systemctl enable docker && systemctl start docker

# Install Docker Compose
apt-get install docker-compose-plugin  # Ubuntu
# or
yum install docker-compose-plugin      # CentOS/Rocky
```

### 2. Clone Repository

```bash
git clone https://github.com/zhuying412/okbox.git
cd okbox
```

### 3. Configure Environment

```bash
cd deploy
cp .env.example .env
# Edit .env with your configuration
nano .env
```

Key configurations:
- `POSTGRES_PASSWORD`: Strong database password
- `SECRET_KEY`: JWT signing key (generate: `openssl rand -hex 32`)
- `MINIO_SECRET_KEY`: MinIO secret key
- `ENCRYPTION_KEY`: Field encryption key (generate: `python -c "import secrets; print(secrets.token_hex(32))"`)

### 4. Generate SSL Certificate

```bash
cd nginx
./generate-cert.sh
cd ..
```

### 5. Start Services

```bash
docker compose up -d
```

### 6. Initialize Database

```bash
# Run migrations
docker compose exec backend alembic upgrade head

# Create admin user
docker compose exec backend python -m okbox.scripts.create_admin
```

### 7. Verify Installation

```bash
# Check all services are running
docker compose ps

# Health check
curl -k https://localhost/api/v1/health
```

## Configuration Reference

| Variable | Description | Default |
|----------|-------------|---------|
| APP_ENV | Environment (development/production) | development |
| DATABASE_URL | PostgreSQL connection string | - |
| REDIS_URL | Redis connection string | redis://redis:6379/0 |
| MINIO_ENDPOINT | MinIO server address | minio:9000 |
| SECRET_KEY | JWT signing secret | - |
| ENCRYPTION_KEY | AES field encryption key | - |

## Firewall Rules

For hospital intranet deployment:

| Port | Service | Access |
|------|---------|--------|
| 443 | HTTPS (Nginx) | Internal network |
| 80 | HTTP (redirect) | Internal network |
| 5432 | PostgreSQL | Backend only |
| 6379 | Redis | Backend only |
| 9000 | MinIO | Backend only |

## Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues.
