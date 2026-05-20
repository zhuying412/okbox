#!/bin/bash
# PostgreSQL backup restore script.
# Usage: ./restore.sh /path/to/backup_file.sql.gz[.enc]

set -euo pipefail

BACKUP_FILE="${1:?Usage: $0 <backup_file>}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-okbox}"
POSTGRES_DB="${POSTGRES_DB:-okbox}"

echo "[$(date)] Starting restore from: ${BACKUP_FILE}"

# Decrypt if encrypted
RESTORE_FILE="${BACKUP_FILE}"
if [[ "${BACKUP_FILE}" == *.enc ]]; then
    if [ -z "${BACKUP_ENCRYPTION_KEY:-}" ]; then
        echo "ERROR: BACKUP_ENCRYPTION_KEY required for encrypted backups"
        exit 1
    fi
    RESTORE_FILE="${BACKUP_FILE%.enc}"
    gpg --decrypt \
        --batch \
        --passphrase "${BACKUP_ENCRYPTION_KEY}" \
        --output "${RESTORE_FILE}" \
        "${BACKUP_FILE}"
    echo "[$(date)] Decrypted backup"
fi

# Restore
echo "[$(date)] Restoring database..."
echo "WARNING: This will overwrite the existing database!"
read -p "Continue? (y/N): " confirm
if [ "${confirm}" != "y" ] && [ "${confirm}" != "Y" ]; then
    echo "Aborted."
    exit 0
fi

pg_restore \
    -h "${POSTGRES_HOST}" \
    -p "${POSTGRES_PORT}" \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    --clean \
    --if-exists \
    "${RESTORE_FILE}"

echo "[$(date)] Restore complete."

# Cleanup decrypted file
if [[ "${BACKUP_FILE}" == *.enc ]] && [ -f "${RESTORE_FILE}" ]; then
    rm -f "${RESTORE_FILE}"
fi
