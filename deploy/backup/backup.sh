#!/bin/bash
# PostgreSQL daily full backup script with encryption.
# Schedule via cron: 0 2 * * * /path/to/backup.sh
#
# Prerequisites:
#   - POSTGRES_USER, POSTGRES_DB, POSTGRES_HOST env vars
#   - BACKUP_DIR, BACKUP_ENCRYPTION_KEY env vars
#   - gpg installed for backup encryption

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/data/backups}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-okbox}"
POSTGRES_DB="${POSTGRES_DB:-okbox}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/okbox_${DATE}.sql.gz"

echo "[$(date)] Starting PostgreSQL backup..."

# Ensure backup directory exists
mkdir -p "${BACKUP_DIR}"

# Full database dump (compressed)
pg_dump \
    -h "${POSTGRES_HOST}" \
    -p "${POSTGRES_PORT}" \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    --format=custom \
    --compress=9 \
    --file="${BACKUP_FILE}"

echo "[$(date)] Dump created: ${BACKUP_FILE}"

# Encrypt backup file if BACKUP_ENCRYPTION_KEY is set
if [ -n "${BACKUP_ENCRYPTION_KEY:-}" ]; then
    ENCRYPTED_FILE="${BACKUP_FILE}.enc"
    gpg --symmetric \
        --cipher-algo AES256 \
        --batch \
        --passphrase "${BACKUP_ENCRYPTION_KEY}" \
        --output "${ENCRYPTED_FILE}" \
        "${BACKUP_FILE}"
    rm -f "${BACKUP_FILE}"
    BACKUP_FILE="${ENCRYPTED_FILE}"
    echo "[$(date)] Backup encrypted: ${BACKUP_FILE}"
fi

# Verify backup file
if [ -f "${BACKUP_FILE}" ]; then
    SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "[$(date)] Backup successful: ${BACKUP_FILE} (${SIZE})"
else
    echo "[$(date)] ERROR: Backup file not found!"
    exit 1
fi

# Remove old backups (retention policy)
echo "[$(date)] Cleaning backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "okbox_*.sql*" -mtime +${RETENTION_DAYS} -delete

echo "[$(date)] Backup complete."
