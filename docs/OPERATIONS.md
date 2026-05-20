# Operations Manual

## Daily Maintenance

### Service Health Check

```bash
# Check all containers
docker compose ps

# Check backend health
curl -k https://localhost/api/v1/health

# Check database connection
docker compose exec postgres pg_isready

# Check Redis
docker compose exec redis redis-cli ping

# Check MinIO
docker compose exec minio mc ready local
```

### Log Viewing

```bash
# View all service logs
docker compose logs -f

# View specific service logs
docker compose logs -f backend
docker compose logs -f postgres
docker compose logs -f nginx

# View last 100 lines
docker compose logs --tail=100 backend
```

### Log Rotation

Docker logs are managed by the Docker daemon. Configure in `/etc/docker/daemon.json`:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "5"
  }
}
```

## Monitoring

### Key Metrics to Monitor

| Metric | Normal Range | Alert Threshold |
|--------|-------------|-----------------|
| CPU Usage | < 70% | > 90% |
| Memory Usage | < 80% | > 90% |
| Disk Usage | < 70% | > 85% |
| DB Connections | < 50% pool | > 80% pool |
| API Response Time | < 200ms p95 | > 1s p95 |
| Pipeline Queue | < 10 pending | > 50 pending |

### Database Monitoring

```bash
# Active connections
docker compose exec postgres psql -U okbox -c "SELECT count(*) FROM pg_stat_activity;"

# Database size
docker compose exec postgres psql -U okbox -c "SELECT pg_size_pretty(pg_database_size('okbox'));"

# Slow queries (enable pg_stat_statements)
docker compose exec postgres psql -U okbox -c "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
```

## Backup & Recovery

See [deploy/backup/README.md](../deploy/backup/README.md) for detailed backup procedures.

### Quick Backup

```bash
# Manual backup
docker compose exec postgres pg_dump -U okbox okbox | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Recovery

```bash
# Stop application
docker compose stop backend

# Restore
gunzip -c backup_20260101.sql.gz | docker compose exec -T postgres psql -U okbox okbox

# Restart
docker compose start backend
```

## Scaling

### Horizontal Scaling

- Add Celery workers: `docker compose up -d --scale celery_worker=3`
- Add read replicas for PostgreSQL (for reporting queries)

### Vertical Scaling

- Increase container resource limits in docker-compose.yml
- Tune PostgreSQL: `shared_buffers`, `work_mem`, `max_connections`
