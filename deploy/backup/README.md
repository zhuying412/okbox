# Backup and Recovery

## Strategy

- **Full backup**: Daily at 02:00 via `backup.sh` (cron)
- **WAL archiving**: Continuous, archived every 5 minutes
- **Retention**: 30 days (configurable via RETENTION_DAYS)
- **Encryption**: AES-256 symmetric encryption of backup files

## Setup

1. Set environment variables:
   ```bash
   export BACKUP_DIR=/data/backups
   export BACKUP_ENCRYPTION_KEY=$(openssl rand -hex 32)
   export POSTGRES_USER=okbox
   export POSTGRES_DB=okbox
   ```

2. Add cron job:
   ```bash
   0 2 * * * /path/to/deploy/backup/backup.sh >> /var/log/okbox-backup.log 2>&1
   ```

3. Configure WAL archiving (add to postgresql.conf):
   ```bash
   cp wal-archive.conf /etc/postgresql/conf.d/
   ```

## Recovery

```bash
# Restore from encrypted backup
export BACKUP_ENCRYPTION_KEY=<your-key>
./restore.sh /data/backups/okbox_20260101_020000.sql.gz.enc
```

## Verification

Regularly verify backups by restoring to a test database:
```bash
POSTGRES_DB=okbox_test ./restore.sh /data/backups/latest.sql.gz.enc
```
