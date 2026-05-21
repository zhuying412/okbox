# Troubleshooting Guide

## Common Issues

### 1. Service Won't Start

**Symptom**: `docker compose up` fails or container exits immediately.

**Diagnosis**:
```bash
docker compose logs <service_name>
docker compose ps
```

**Common causes**:
- Port already in use: `lsof -i :<port>`
- Missing .env configuration
- Insufficient disk space: `df -h`
- Permission issues on mounted volumes

**Resolution**:
```bash
# Check port conflicts
ss -tlnp | grep -E "(5432|6379|9000|8000|80)"

# Fix volume permissions
chmod -R 777 /path/to/data/volumes  # Dev only; use proper UID in prod

# Rebuild from scratch
docker compose down -v
docker compose up -d
```

### 2. Database Connection Error

**Symptom**: Backend reports "connection refused" or "password authentication failed".

**Diagnosis**:
```bash
docker compose exec postgres pg_isready
docker compose logs postgres
```

**Resolution**:
- Verify DATABASE_URL in .env matches POSTGRES_USER/POSTGRES_PASSWORD
- Check PostgreSQL is healthy: `docker compose exec postgres psql -U okbox -c "SELECT 1;"`
- Reset: `docker compose down -v` (WARNING: deletes data)

### 3. Pipeline Task Stuck in "Pending"

**Symptom**: Tasks remain in "pending" status indefinitely.

**Diagnosis**:
```bash
# Check Celery workers
docker compose logs celery_worker

# Check Redis broker
docker compose exec redis redis-cli LLEN celery
```

**Resolution**:
- Restart Celery worker: `docker compose restart celery_worker`
- Check Redis connectivity
- Verify miniwdl is installed in worker image

### 4. File Upload Fails

**Symptom**: 413 error or upload timeout.

**Resolution**:
- Check Nginx `client_max_body_size` setting
- Increase proxy timeouts in nginx config
- Verify MinIO has available storage: `docker compose exec minio mc admin info local`

### 5. Report PDF Generation Fails

**Symptom**: Report stays in "generating" status.

**Diagnosis**:
```bash
docker compose logs backend | grep "PDF"
```

**Resolution**:
- Ensure WeasyPrint is installed: `docker compose exec backend pip show weasyprint`
- Install Chinese fonts for CJK support
- Check write permissions to reports output directory

### 6. Connection Issues

**Symptom**: Unable to access application from browser.

**Resolution**:
- Verify Nginx container is running: `docker compose ps nginx`
- Check if port 80 is available: `ss -tlnp | grep :80`
- If HTTPS is required, configure it at the external reverse proxy / load balancer layer

## Log Analysis

### Audit Log Queries

```sql
-- Failed login attempts
SELECT username, ip_address, created_at
FROM audit_logs
WHERE path = '/api/v1/auth/login' AND status_code = 401
ORDER BY created_at DESC;

-- Recent write operations
SELECT action, resource_type, username, created_at
FROM audit_logs
WHERE action IN ('POST', 'PUT', 'DELETE')
ORDER BY created_at DESC
LIMIT 50;
```

### Performance Investigation

```bash
# API response times (from Nginx access log)
docker compose exec nginx cat /var/log/nginx/access.log | awk '{print $NF}' | sort -n | tail -20

# Database slow queries
docker compose exec postgres psql -U okbox -c "
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 100
ORDER BY mean_exec_time DESC
LIMIT 10;"
```

## Recovery Steps

### Complete System Recovery

1. Restore database from backup
2. Verify MinIO data integrity
3. Restart all services
4. Run health checks
5. Verify audit log continuity

### Data Corruption

If data corruption is detected:
1. Stop all services immediately
2. Identify the last known-good backup
3. Restore from backup
4. Replay WAL logs to point-in-time (if available)
5. Verify data integrity
6. Resume services
