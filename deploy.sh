#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="/opt/educational-center/educational_center"
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE="${ENV_FILE:-.env.prod}"

cd "$PROJECT_DIR"

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing environment file: $PROJECT_DIR/$ENV_FILE" >&2
  exit 1
fi

export ENV_FILE
COMPOSE=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")

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
