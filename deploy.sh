#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="/opt/educational-center/educational_center"
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE="${ENV_FILE:-.env.prod}"
BACKUP_DIR="${BACKUP_DIR:-/opt/educational-center/backups}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

cd "$PROJECT_DIR"

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing environment file: $PROJECT_DIR/$ENV_FILE" >&2
  exit 1
fi

export ENV_FILE
COMPOSE=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")

case "$BACKUP_RETENTION_DAYS" in
  ''|*[!0-9]*)
    echo "BACKUP_RETENTION_DAYS must be a non-negative integer." >&2
    exit 1
    ;;
esac

mkdir -p "$BACKUP_DIR"

echo "=== Starting database for backup ==="
"${COMPOSE[@]}" up -d db

backup_file="$BACKUP_DIR/educational_center_$(date -u +%Y%m%dT%H%M%SZ).dump"
tmp_backup_file="$backup_file.tmp"
trap 'rm -f "$tmp_backup_file"' EXIT

echo "=== Creating database backup ==="
"${COMPOSE[@]}" exec -T db sh -c 'until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do sleep 2; done'
"${COMPOSE[@]}" exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$tmp_backup_file"
mv "$tmp_backup_file" "$backup_file"
echo "Backup saved to $backup_file"

echo "=== Removing old database backups ==="
find "$BACKUP_DIR" -type f -name 'educational_center_*.dump' -mtime +"$BACKUP_RETENTION_DAYS" -delete

echo "=== Fetching latest code ==="
git fetch --prune origin main
git reset --hard origin/main

echo "=== Building production images ==="
"${COMPOSE[@]}" build

echo "=== Starting production services ==="
"${COMPOSE[@]}" up -d --remove-orphans

echo "=== Removing unused Docker images ==="
docker image prune -f

echo "=== Deployment completed successfully ==="
