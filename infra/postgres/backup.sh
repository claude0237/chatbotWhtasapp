#!/bin/bash
# Automated PostgreSQL backup script

set -euo pipefail

BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="${POSTGRES_DB:-chatbot_prod}"
DB_USER="${POSTGRES_USER:-postgres}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"

mkdir -p "$BACKUP_DIR"

BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz"

echo "[$(date)] Starting backup of $DB_NAME..."

pg_dump -U "$DB_USER" -d "$DB_NAME" \
    --no-password \
    --format=custom \
    --compress=9 \
    | gzip > "$BACKUP_FILE"

echo "[$(date)] Backup completed: $BACKUP_FILE ($(du -sh "$BACKUP_FILE" | cut -f1))"

# Remove old backups
find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
echo "[$(date)] Cleaned up backups older than ${RETENTION_DAYS} days"

# Optional: upload to S3
if [ -n "${AWS_S3_BACKUP_BUCKET:-}" ]; then
    aws s3 cp "$BACKUP_FILE" "s3://${AWS_S3_BACKUP_BUCKET}/postgres/${DB_NAME}_${TIMESTAMP}.sql.gz"
    echo "[$(date)] Uploaded backup to S3"
fi
