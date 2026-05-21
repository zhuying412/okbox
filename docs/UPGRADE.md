# Upgrade Guide

## Version Upgrade Process

### Pre-Upgrade Checklist

- [ ] Read release notes for the target version
- [ ] Verify hardware/software compatibility
- [ ] Create full database backup
- [ ] Document current version and configuration
- [ ] Notify users of maintenance window
- [ ] Prepare rollback plan

### Upgrade Steps

#### 1. Backup Current State

```bash
# Full database backup
docker compose exec postgres pg_dump -U okbox -Fc okbox > pre-upgrade-backup.dump

# Backup configuration
cp deploy/.env deploy/.env.backup
```

#### 2. Pull New Code

```bash
git fetch origin
git checkout v<new-version>
```

#### 3. Review Changes

```bash
# Check for new environment variables
diff deploy/.env.example deploy/.env

# Check for new dependencies
git diff v<old-version>..v<new-version> -- packages/backend/pyproject.toml
```

#### 4. Stop Services (Maintenance Window)

```bash
docker compose stop backend
# Keep database running for migrations
```

#### 5. Run Database Migrations

```bash
docker compose exec backend alembic upgrade head
```

#### 6. Rebuild and Start

```bash
docker compose build
docker compose up -d
```

#### 7. Verify

```bash
# Health check
curl http://localhost/api/v1/health

# Check logs for errors
docker compose logs --tail=50 backend

# Run smoke tests
curl http://localhost/api/v1/auth/login -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"<pwd>"}'
```

### Rollback Procedure

If issues are found after upgrade:

```bash
# 1. Stop services
docker compose down

# 2. Restore code
git checkout v<old-version>

# 3. Restore database
docker compose up -d postgres
docker compose exec postgres pg_restore -U okbox -d okbox --clean pre-upgrade-backup.dump

# 4. Rebuild and restart
docker compose build
docker compose up -d

# 5. Verify rollback
curl http://localhost/api/v1/health
```

## Data Migration

For major version upgrades that change database schema:

1. Export data in structured format before upgrade
2. Run migration scripts provided in release notes
3. Verify data integrity after migration
4. Update traceability matrix if schema changes affect validated functions
